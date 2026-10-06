import os
import tempfile
import unittest

import mdlinkcheck as m


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        p = os.path.join(self.tmp.name, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p


class Tests(Base):
    def test_missing_file(self):
        p = self.write("a.md", "ok\n[x](nope.md)\n")
        self.assertEqual([n for n, _ in m.check_file(p)], [2])

    def test_existing_file(self):
        self.write("b.md", "# B\n")
        p = self.write("a.md", "[x](b.md) [y](./b.md#b)\n")
        self.assertEqual(m.check_file(p), [])

    def test_bad_anchor(self):
        p = self.write("a.md", "# Hello\n[x](#nothere)\n")
        probs = m.check_file(p)
        self.assertEqual(len(probs), 1)
        self.assertIn("anchor", probs[0][1])

    def test_bad_anchor_other_file(self):
        self.write("b.md", "# B\n")
        p = self.write("a.md", "[x](b.md#zzz)\n")
        self.assertEqual(len(m.check_file(p)), 1)

    def test_good_anchor(self):
        p = self.write("a.md", "# Hello, World! (v2)\n[x](#hello-world-v2)\n")
        self.assertEqual(m.check_file(p), [])

    def test_code_fence_ignored(self):
        p = self.write("a.md", "```\n[x](nope.md)\n# Fake\n```\n~~~\n[y](no.md)\n~~~\n"
                       "`[z](nope.md)`\n")
        self.assertEqual(m.check_file(p), [])

    def test_external_ignored(self):
        p = self.write("a.md", "[a](https://x.invalid/y) [b](mailto:a@b.c)\n")
        self.assertEqual(m.check_file(p), [])

    def test_duplicate_slugs(self):
        text = "# Foo\n## Foo\n### Foo\n"
        self.assertEqual(m.heading_slugs(text), {"foo", "foo-1", "foo-2"})
        p = self.write("a.md", text + "[a](#foo-1) [b](#foo-2) [c](#foo-3)\n")
        self.assertEqual([n for n, _ in m.check_file(p)], [4])

    def test_main_exit_codes(self):
        good = self.write("g.md", "# T\n[a](#t)\n")
        bad = self.write("b.md", "[a](missing.md)\n")
        self.assertEqual(m.main([good]), 0)
        self.assertEqual(m.main([bad]), 1)
        self.assertEqual(m.main([self.tmp.name]), 1)


if __name__ == "__main__":
    unittest.main()
