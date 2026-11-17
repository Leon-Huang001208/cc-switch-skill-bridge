import io
import unittest
from zipfile import ZipFile

from sync import graphify_files, vetter_files

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

    def test_vetter_rejects_unexpected_executable(self):
        skill=b"---\nname: skill-vetter\n---\n"
        with self.assertRaises(ValueError):
            vetter_files(archive({"SKILL.md":skill,"run.sh":"oops"}),skill,"1.0.0")

    def test_vetter_requires_exact_official_bytes(self):
        with self.assertRaises(ValueError):
            vetter_files(archive({"SKILL.md":"not canonical"}),b"canonical","1.0.0")

    def test_vetter_preserves_instruction_bytes(self):
        skill=b"---\nname: skill-vetter\n---\n"
        out=vetter_files(archive({"SKILL.md":skill,"skill-card.md":"MIT-0"}),skill,"1.0.0")
        self.assertEqual(out["SKILL.md"],skill)
        self.assertEqual(out["skill-card.md"],b"MIT-0")

if __name__ == "__main__":
    unittest.main()
