import io
import unittest
from zipfile import ZipFile

from sync import graphify_files

def archive(files):
    out = io.BytesIO()
    with ZipFile(out,"w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()

class BridgeTests(unittest.TestCase):
    def test_graphify_renames_skill_and_excludes_runtime(self):
        data=archive({"graphify/skill-codex.md":"---\nname: graphify\n---\n",
                      "graphify/skills/codex/references/query.md":"query docs",
                      "graphify/__init__.py":"runtime",
                      "graphifyy-9.0.0.dist-info/licenses/LICENSE":"license"})
        out=graphify_files(data,"9.0.0")
        self.assertEqual(out["SKILL.md"],b"---\nname: graphify\n---\n")
        self.assertEqual(out["references/query.md"],b"query docs")
        self.assertNotIn("__init__.py",out)
        self.assertEqual(out["LICENSE"],b"license")

if __name__ == "__main__":
    unittest.main()
