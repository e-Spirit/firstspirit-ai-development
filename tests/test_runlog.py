"""Offline tests for scripts/runlog.py: python3 -m unittest discover -s tests"""
import importlib.util, os, pathlib, shutil, subprocess, sys, tempfile, unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = HERE / "scripts" / "runlog.py"
spec = importlib.util.spec_from_file_location("runlog", SCRIPT)
runlog = importlib.util.module_from_spec(spec); spec.loader.exec_module(runlog)


def run(d, *args, now=None):
    env = dict(os.environ, RUNLOG_DIR=str(d))
    env.pop("RUNLOG_PROJECT", None)
    if now: env["RUNLOG_NOW"] = now
    return subprocess.run([sys.executable, str(SCRIPT)] + list(args), capture_output=True, text=True, env=env)


class Redact(unittest.TestCase):
    def test_credentials_and_hosts(self):
        r = runlog.redact("fs-cli -h customer.example.hosting -u jane.doe -pwd s3cr3t! -p acme-prod failed")
        for leak in ("customer", "jane", "s3cr3t", "acme"): self.assertNotIn(leak, r)
        r = runlog.redact("GET https://user:pw@tenant.eu-central-1.example.com:8443/rest/v1/x?token=abc#frag -> 401")
        self.assertIn("https://<host>/rest/v1/x", r)
        for leak in ("tenant", "pw", "abc", "frag", "8443"): self.assertNotIn(leak, r)
        r = runlog.redact("Authorization: Bearer abcDEF123456789 and password=hunter2 and FS_PASSWORD=x")  # secret-scan: ignore
        for leak in ("abcDEF", "hunter2"): self.assertNotIn(leak, r)  # secret-scan: ignore

    def test_paths_ids_and_addresses(self):
        r = runlog.redact("read /Users/jane/Documents/x/y.xml and /home/bob/z and C:\\Users\\Alice\\f")
        for leak in ("jane", "bob", "Alice"): self.assertNotIn(leak, r)
        r = runlog.redact("project 123e4567-e89b-12d3-a456-426614174000 at 10.1.2.3 mail a.b@corp.example.org key AbCdEf0123456789AbCdEf0123456789")
        for leak in ("123e4567", "10.1.2.3", "a.b@", "AbCdEf0123"): self.assertNotIn(leak, r)
        self.assertIn("<uuid>", r); self.assertIn("<ip>", r); self.assertIn("<email>", r); self.assertIn("<token>", r)

    def test_user_and_machine_names(self):
        with mock.patch.object(runlog.getpass, "getuser", return_value="jdoe"), \
             mock.patch.object(runlog.socket, "gethostname", return_value="Laptop-Pro.local"):
            r = runlog.redact("built by jdoe on Laptop-Pro in the repo")
        self.assertNotIn("jdoe", r); self.assertNotIn("Laptop", r)

    def test_redaction_is_idempotent(self):
        for s in ("boom at https://secret.example.com/x?k=1", "-h a.b.example.com -pwd x", "ids 123e4567-e89b-12d3-a456-426614174000 10.0.0.1"):
            once = runlog.redact(s); self.assertEqual(runlog.redact(once), once)

    def test_keeps_what_is_useful(self):
        s = "import failed: element sections/hero not found (HTTP 404) in 12 files, rule INFO"
        self.assertEqual(runlog.redact(s), s)

    def test_one_line_and_length(self):
        r = runlog.redact("a\nb\tc" + "x " * 400)
        self.assertNotIn("\n", r); self.assertNotIn("\t", r); self.assertLessEqual(len(r), runlog.MAXLEN)


class Log(unittest.TestCase):
    def setUp(self): self.d = pathlib.Path(tempfile.mkdtemp())
    def tearDown(self): shutil.rmtree(self.d, ignore_errors=True)
    def lines(self, name="session"): return (self.d / (name + ".log")).read_text().splitlines()

    def test_duration_from_start_to_end(self):
        run(self.d, "start", "import", "dev target", now="2026-10-19T10:00:00Z")
        run(self.d, "end", "import", now="2026-10-19T10:01:05Z")
        f = self.lines()[-1].split("\t"); self.assertEqual((f[1], f[2], f[3]), ("ok", "import", "65"))

    def test_error_handling_and_resolution(self):
        run(self.d, "start", "verify", now="2026-10-19T10:00:00Z")
        run(self.d, "error", "verify", "--handled", "agent", "--fix", "added the missing default", "template log: undefined method", now="2026-10-19T10:00:30Z")
        run(self.d, "error", "import", "--handled", "open", "HTTP 500 on channel write", now="2026-10-19T10:02:00Z")
        run(self.d, "resolve", "import", "--by", "human", "asked for a retry with another header", now="2026-10-19T10:05:00Z")
        run(self.d, "end", "verify", "--status", "fail", now="2026-10-19T10:06:00Z")
        r = run(self.d, "summary")
        self.assertIn("1 handled by the agent", r.stdout); self.assertIn("0 needed a person, 1 logged as open (0 still unresolved)", r.stdout)
        self.assertIn("resolved: 0 by the agent, 1 by a person", r.stdout)
        res = [l.split("\t") for l in self.lines() if "\tresolved\t" in l][0]; self.assertEqual(res[3], "180")
        self.assertIn("fix: added the missing default", self.lines()[1])

    def test_unresolved_open_error_is_listed(self):
        run(self.d, "error", "seed", "--handled", "open", "exit code 1", now="2026-10-19T10:00:00Z")
        self.assertIn("1 still unresolved", run(self.d, "summary").stdout)

    def test_run_wraps_a_command_and_keeps_its_exit_code(self):
        ok = run(self.d, "run", "build", "--", "sh", "-c", "echo fine")
        self.assertEqual(ok.returncode, 0); self.assertIn("fine", ok.stdout)
        bad = run(self.d, "run", "build", "--", "sh", "-c", "echo 'boom at https://secret.example.com/x?k=1'; exit 3")
        self.assertEqual(bad.returncode, 3)
        text = (self.d / "session.log").read_text()
        self.assertIn("exit code 3", text); self.assertNotIn("secret.example", text); self.assertNotIn("k=1", text)
        self.assertEqual(run(self.d, "check").returncode, 0)

    def test_check_finds_an_unredacted_line_and_a_malformed_one(self):
        (self.d / "session.log").write_text("2026-10-19T10:00:00Z\tnote\tx\t\t-\tmail me at a.b@corp.example.org\n")
        r = run(self.d, "check"); self.assertEqual(r.returncode, 1); self.assertIn("redaction", r.stdout)
        (self.d / "session.log").write_text("garbage\n")
        self.assertEqual(run(self.d, "check").returncode, 1)

    def test_check_skips_without_a_log(self):
        r = run(self.d, "check"); self.assertEqual(r.returncode, 0); self.assertIn("SKIP", r.stdout)

    def test_log_name_and_step_are_sanitised(self):
        run(self.d, "--project", "../evil name", "note", "a b/c", "x")
        files = [p.name for p in self.d.iterdir()]
        self.assertEqual(files, ["..-evil-name.log"]); self.assertIn("\ta-b-c\t", (self.d / files[0]).read_text())

    def test_a_logging_failure_never_breaks_the_caller(self):
        blocked = self.d / "file"; blocked.write_text("x")
        r = run(blocked / "sub", "note", "x", "y")
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
