"""Offline tests for scripts/check-skills.py: python3 -m unittest discover -s tests"""
import importlib.util, os, pathlib, shutil, subprocess, sys, tempfile, unittest

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = HERE / "scripts" / "check-skills.py"
spec = importlib.util.spec_from_file_location("check_skills", SCRIPT)
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)

STAMPED = """---
name: firstspirit-rest-api
description: >
  FirstSpirit REST API expert for performing CMS operations via curl.
  Second line of the description.
metadata:
  source-commit: "1e54562"
  published: "2026-10-30"
  toolkit-version: "0.7.0"
---
# body
"""
UNSTAMPED = """---
name: firstspirit-template-design
description: "Design principles for FirstSpirit templates."
---
"""
OTHER = """---
name: pdf
description: Read and write PDF files.
---
"""


def skill(base, rel, text, files=()):
    d = base / rel
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(text, encoding="utf-8")
    for f in files:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("x", encoding="utf-8")
    return d


class Frontmatter(unittest.TestCase):
    def test_stamped_and_folded_description(self):
        with tempfile.TemporaryDirectory() as t:
            d = skill(pathlib.Path(t), "a", STAMPED)
            fm = cs.frontmatter(d / "SKILL.md")
        self.assertEqual(fm["name"], "firstspirit-rest-api")
        self.assertIn("Second line", fm["description"])
        self.assertEqual(fm["metadata"], {"source-commit": "1e54562", "published": "2026-10-30", "toolkit-version": "0.7.0"})

    def test_unstamped_quoted_description(self):
        with tempfile.TemporaryDirectory() as t:
            fm = cs.frontmatter(skill(pathlib.Path(t), "b", UNSTAMPED) / "SKILL.md")
        self.assertEqual(fm["description"], "Design principles for FirstSpirit templates.")
        self.assertEqual(fm["metadata"], {})

    def test_firstspirit_detection(self):
        self.assertTrue(cs.is_firstspirit({"name": "firstspirit-x", "description": ""}))
        self.assertTrue(cs.is_firstspirit({"name": "caas-tool", "description": "Reads FirstSpirit content"}))
        self.assertFalse(cs.is_firstspirit({"name": "pdf", "description": "Read PDF files."}))


class Scan(unittest.TestCase):
    def setUp(self):
        self.t = pathlib.Path(tempfile.mkdtemp())
        self.plugin = self.t / "plugins" / "cache" / "mk" / "toolkit" / "0.7.0"
        (self.plugin / ".claude-plugin").mkdir(parents=True)
        (self.plugin / ".claude-plugin" / "plugin.json").write_text('{"version": "0.7.0"}')
        skill(self.plugin, "skills/project/firstspirit-rest-api", STAMPED, ["references/content-templates.md"])
        skill(self.plugin, "skills/templating/firstspirit-template-design", UNSTAMPED,
              ["references/cutting-an-artifact.md", "references/choosing-an-input-component.md", "references/output-conventions.md"])
        skill(self.t / "home-skills", "pdf", OTHER)
        # a symlink loop must not hang the walk
        os.symlink(self.t / "home-skills", self.t / "home-skills" / "loop")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def run_script(self, *args):
        env = dict(os.environ, FS_SKILLS_PATH=os.pathsep.join([str(self.t / "home-skills"), str(self.plugin)]))
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env, timeout=60)

    def test_find_skills_follows_symlinks_once(self):
        found = cs.find_skills([self.t / "home-skills", self.plugin])
        self.assertEqual(sorted(s["name"] for s in found), ["firstspirit-rest-api", "firstspirit-template-design", "pdf"])

    def test_list_shows_stamp_plugin_version_and_lock_mark(self):
        r = self.run_script()
        self.assertIn("2 FirstSpirit skill(s) found", r.stdout)
        self.assertIn("firstspirit-rest-api", r.stdout)
        self.assertIn("0.7.0 (1e54562, 2026-10-30)", r.stdout)
        self.assertIn("0.7.0 (plugin, unstamped)", r.stdout)
        self.assertIn("lock: published", r.stdout)
        self.assertNotIn("pdf", r.stdout)
        self.assertIn("FAIL  firstspirit-templating-reference (published): not installed", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_all_lists_other_skills_and_lock_only_lists_none(self):
        self.assertIn("pdf", self.run_script("--all").stdout)
        self.assertIn("not in lock", self.run_script("--all").stdout)
        out = self.run_script("--lock").stdout
        self.assertNotIn("found under", out)
        self.assertIn("OK    firstspirit-rest-api 0.7.0 at", out)

    def test_old_stamp_warns(self):
        d = self.plugin / "skills" / "project" / "firstspirit-rest-api"
        (d / "SKILL.md").write_text(STAMPED.replace('"0.7.0"', '"0.5.0"'), encoding="utf-8")
        out = self.run_script("--lock").stdout
        self.assertIn("WARN  firstspirit-rest-api: version 0.5.0 is older than this repository expects (0.6.0 or newer)", out)


class Versions(unittest.TestCase):
    def test_tuple_and_comparison(self):
        self.assertEqual(cs.version_tuple("0.7.0-beta"), (0, 7, 0))
        self.assertIsNone(cs.version_tuple("unknown"))
        self.assertTrue(cs.older_than_expected("0.5.2", "0.6.0 or newer"))
        self.assertFalse(cs.older_than_expected("0.7.0", "0.6.0 or newer"))
        self.assertIsNone(cs.older_than_expected(None, "0.6.0 or newer"))


if __name__ == "__main__":
    unittest.main()
