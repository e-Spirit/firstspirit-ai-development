import importlib.util, os, pathlib, tempfile, unittest

SPEC = importlib.util.spec_from_file_location(
    "check_connection", pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check-connection.py")
cc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cc)


class ReadFile(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "c.env"
            f.write_text(text, encoding="utf-8")
            return cc.read_file(f)

    def test_plain_and_quoted(self):
        values, trailing = self.read("A='x'\nB=\"y\"\nC=z\n# note\n")
        self.assertEqual(values, {"A": "x", "B": "y", "C": "z"})
        self.assertEqual(trailing, set())

    def test_comment_after_value_is_flagged_and_stripped(self):
        values, trailing = self.read("ID='123456'  # my project\nU=bob #x\n")
        self.assertEqual(values["ID"], "123456")
        self.assertEqual(values["U"], "bob")
        self.assertEqual(trailing, {"ID", "U"})

    def test_hash_inside_a_password_is_kept(self):
        values, trailing = self.read("P='pa#ss'\nQ=a#b\n")
        self.assertEqual(values, {"P": "pa#ss", "Q": "a#b"})
        self.assertEqual(trailing, set())


class Locate(unittest.TestCase):
    def test_argument_beats_variable(self):
        os.environ["FS_CONNECTION_FILE"] = "/somewhere/else.env"
        try:
            self.assertEqual(cc.locate("/x.env")[0], pathlib.Path("/x.env"))
            self.assertEqual(cc.locate()[0], pathlib.Path("/somewhere/else.env"))
        finally:
            del os.environ["FS_CONNECTION_FILE"]

    def test_default_is_relative_to_the_script(self):
        os.environ.pop("FS_CONNECTION_FILE", None)
        path, why = cc.locate()
        if "repository root" in why:
            self.assertEqual(path, cc.ROOT / "connection.env")


if __name__ == "__main__":
    unittest.main()
