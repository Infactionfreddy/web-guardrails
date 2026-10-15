#!/usr/bin/env python3
"""Tests für guard.py. Ausführen: python3 -m unittest discover -s tests -v"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(ROOT, "plugins", "web-guardrails", "scripts", "guard.py")


def run(args, cwd, stdin=None, env=None):
    e = dict(os.environ)
    e.pop("CLAUDE_PROJECT_DIR", None)
    e.update(env or {})
    return subprocess.run([sys.executable, GUARD] + args, cwd=cwd, input=stdin,
                          capture_output=True, text=True, env=e)


def write(base, rel, text):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="wg-test-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def hook(self, mode, payload, session="s1"):
        payload = dict(payload, session_id=session + self.dir, cwd=self.dir)
        return run([mode], self.dir, stdin=json.dumps(payload), env={"CLAUDE_PROJECT_DIR": self.dir})


class StackDetection(Base):
    def test_plain_project_has_no_stack(self):
        write(self.dir, "index.html", "<h1>hi</h1>")
        self.assertEqual(run(["stacks", self.dir], self.dir).stdout.strip(), "-")

    def test_theme_detected(self):
        write(self.dir, "wp-content/themes/royals/style.css", "/*\nTheme Name: Royals\n*/")
        self.assertEqual(run(["stacks", self.dir], self.dir).stdout.strip(), "wordpress")

    def test_plugin_header_detected(self):
        write(self.dir, "my-plugin.php", "<?php\n/**\n * Plugin Name: My Plugin\n */")
        self.assertEqual(run(["stacks", self.dir], self.dir).stdout.strip(), "wordpress")

    def test_config_overrides(self):
        write(self.dir, ".web-guardrails.json", json.dumps({"stacks": ["wordpress"]}))
        self.assertEqual(run(["stacks", self.dir], self.dir).stdout.strip(), "wordpress")


class Context(Base):
    def test_common_only(self):
        out = run(["context"], self.dir, env={"CLAUDE_PROJECT_DIR": self.dir}).stdout
        self.assertIn("Projektkonventionen", out)
        self.assertNotIn("WordPress-spezifische", out)
        self.assertFalse(out.lstrip().startswith("{"))  # muss als Klartext in den Kontext

    def test_wordpress_and_project_context(self):
        write(self.dir, "wp-config.php", "<?php")
        write(self.dir, ".web-guardrails.json", json.dumps({"context": {"Consent-Tool": "Borlabs"}}))
        out = run(["context"], self.dir, env={"CLAUDE_PROJECT_DIR": self.dir}).stdout
        self.assertIn("WordPress-spezifische", out)
        self.assertIn("Consent-Tool: Borlabs", out)
        self.assertIn("/web-guardrails:init", out)
        self.assertLess(len(out), 10000)  # Hook-Kontext ist auf 10.000 Zeichen begrenzt


class PreHook(Base):
    def test_blocks_google_fonts_in_css(self):
        p = os.path.join(self.dir, "style.css")
        r = self.hook("pre", {"tool_name": "Write", "tool_input": {
            "file_path": p, "content": "@import url(https://fonts.googleapis.com/css2?family=Inter);"}})
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("google_fonts_remote", out["permissionDecisionReason"])

    def test_blocks_sql_injection_in_edit(self):
        p = os.path.join(self.dir, "functions.php")
        r = self.hook("pre", {"tool_name": "Edit", "tool_input": {
            "file_path": p, "old_string": "x",
            "new_string": '$wpdb->get_results( "SELECT * FROM t WHERE id=" . $_GET["id"] );'}})
        self.assertIn("superglobal_in_sql", r.stdout)

    def test_blocks_multiedit_echo(self):
        p = os.path.join(self.dir, "page.php")
        r = self.hook("pre", {"tool_name": "MultiEdit", "tool_input": {
            "file_path": p, "edits": [{"old_string": "a", "new_string": "echo $_GET['q'];"}]}})
        self.assertIn("superglobal_echo", r.stdout)

    def test_php_rule_not_applied_to_js(self):
        p = os.path.join(self.dir, "app.js")
        r = self.hook("pre", {"tool_name": "Write", "tool_input": {
            "file_path": p, "content": "// echo $_GET['q'];"}})
        self.assertEqual(r.stdout, "")

    def test_allows_clean_and_suppressed(self):
        p = os.path.join(self.dir, "functions.php")
        for content in ["wp_enqueue_style( 'f', get_theme_file_uri( 'assets/fonts/inter.css' ) );",
                        "// fonts.googleapis.com dsgvo-ok: nur Kommentar in Doku"]:
            r = self.hook("pre", {"tool_name": "Write", "tool_input": {"file_path": p, "content": content}})
            self.assertEqual(r.stdout, "", content)
            self.assertEqual(r.returncode, 0)

    def test_ignores_markdown_and_vendor(self):
        for rel in ["README.md", "vendor/lib/x.php"]:
            r = self.hook("pre", {"tool_name": "Write", "tool_input": {
                "file_path": os.path.join(self.dir, rel), "content": "fonts.googleapis.com"}})
            self.assertEqual(r.stdout, "", rel)

    def test_broken_input_never_blocks(self):
        r = run(["pre"], self.dir, stdin="not json")
        self.assertEqual((r.returncode, r.stdout), (0, ""))


class PostHook(Base):
    def test_warns_once_per_session(self):
        p = write(self.dir, "footer.html",
                  '<iframe src="https://www.youtube-nocookie.com/embed/abc"></iframe>\n'
                  '<script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>\n')
        payload = {"tool_name": "Edit", "tool_input": {"file_path": p}}
        r1 = self.hook("post", payload)
        self.assertEqual(r1.returncode, 2)
        self.assertIn("video_embed", r1.stderr)
        self.assertIn("analytics_tracking", r1.stderr)
        r2 = self.hook("post", payload)
        self.assertEqual(r2.returncode, 0)

    def test_wordpress_rules_only_with_stack(self):
        p = write(self.dir, "comments.php", "<?php echo get_avatar( $c );")
        self.assertEqual(self.hook("post", {"tool_input": {"file_path": p}}, session="a").returncode, 0)
        write(self.dir, "wp-config.php", "<?php")
        r = self.hook("post", {"tool_input": {"file_path": p}}, session="b")
        self.assertEqual(r.returncode, 2)
        self.assertIn("gravatar", r.stderr)

    def test_allow_hosts_and_disable_rules(self):
        write(self.dir, ".web-guardrails.json", json.dumps({
            "allow_hosts": ["cdn.jsdelivr.net"], "disable_rules": ["video_embed"]}))
        p = write(self.dir, "a.html",
                  '<script src="https://cdn.jsdelivr.net/npm/x.js"></script>\n'
                  '<iframe src="https://www.youtube.com/embed/x"></iframe>\n')
        self.assertEqual(self.hook("post", {"tool_input": {"file_path": p}}).returncode, 0)


class Scan(Base):
    def setUp(self):
        super().setUp()
        write(self.dir, "wp-content/themes/t/style.css", "/*\nTheme Name: T\n*/\n")
        write(self.dir, "wp-content/themes/t/functions.php",
              "<?php\nwp_enqueue_style( 'f', 'https://fonts.googleapis.com/css2?family=Inter' );\n")
        write(self.dir, "wp-content/themes/t/footer.php", '<iframe src="https://player.vimeo.com/video/1"></iframe>\n')
        write(self.dir, "node_modules/x/index.js", "fonts.googleapis.com")

    def test_scan_exit_and_counts(self):
        r = run(["scan", "."], self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("1 BLOCK", r.stdout)
        self.assertNotIn("node_modules", r.stdout)

    def test_github_annotations(self):
        r = run(["scan", "--github", "."], self.dir)
        self.assertIn("::error file=wp-content/themes/t/functions.php,line=2", r.stdout)
        self.assertIn("::warning file=wp-content/themes/t/footer.php,line=1", r.stdout)

    def test_strict(self):
        os.remove(os.path.join(self.dir, "wp-content/themes/t/functions.php"))
        self.assertEqual(run(["scan", "."], self.dir).returncode, 0)
        self.assertEqual(run(["scan", "--strict", "."], self.dir).returncode, 1)


@unittest.skipUnless(shutil.which("git"), "git fehlt")
class GitHook(Base):
    def git(self, *a):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t"] + list(a),
                              cwd=self.dir, capture_output=True, text=True)

    def test_pre_commit_blocks_and_allows(self):
        self.git("init", "-q")
        r = run(["install-git-hook"], self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        write(self.dir, "ok.css", "body{}")
        self.git("add", "ok.css")
        self.assertEqual(self.git("commit", "-qm", "ok").returncode, 0)
        write(self.dir, "bad.css", "@import url(https://fonts.googleapis.com/css2?family=X);")
        self.git("add", "bad.css")
        c = self.git("commit", "-qm", "bad")
        self.assertNotEqual(c.returncode, 0)
        self.assertIn("google_fonts_remote", c.stdout + c.stderr)
        # nur gestagter Inhalt zählt: Fix im Working Tree ohne add -> weiterhin blockiert
        write(self.dir, "bad.css", "body{}")
        self.assertNotEqual(self.git("commit", "-qm", "bad").returncode, 0)
        self.git("add", "bad.css")
        self.assertEqual(self.git("commit", "-qm", "fixed").returncode, 0)


if __name__ == "__main__":
    unittest.main()
