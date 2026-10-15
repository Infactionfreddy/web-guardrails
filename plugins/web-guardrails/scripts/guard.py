#!/usr/bin/env python3
"""
web-guardrails: DSGVO- und Sicherheits-Wächter für Webprojekte (Claude Code Plugin, Git-Hook, CI).

Befehle
  context               SessionStart-Hook: gibt die passenden Projektregeln aus (stdout -> Claude-Kontext)
  pre                   PreToolUse-Hook (Write/Edit/MultiEdit): blockiert harte Verstöße vor dem Schreiben
  post                  PostToolUse-Hook: meldet Drittanbieter-Verbindungen nach dem Schreiben (exit 2)
  scan [opts] [pfade]   Audit von Dateien/Ordnern. Exit 1 bei BLOCK-Funden
        --staged          nur die in Git gestagten Inhalte prüfen (für pre-commit)
        --github          Funde zusätzlich als GitHub-Annotations ausgeben
        --strict          auch WARN-Funde lassen den Scan scheitern
  stacks [pfad]         erkannte Stacks ausgeben
  install-git-hook      pre-commit-Hook im aktuellen Git-Repo installieren

Ausnahme für eine Zeile: Kommentar `dsgvo-ok: <Begründung>` in derselben Zeile.
Projekt-Konfiguration (optional): .web-guardrails.json im Projektwurzelverzeichnis
  {
    "stacks": ["wordpress"],            # überschreibt die Auto-Erkennung
    "allow_hosts": ["cdn.meinverein.de"],  # eigene Domains, die nicht gemeldet werden
    "disable_rules": ["gravatar"],
    "skip_dirs": ["legacy"],
    "context": {"Consent-Tool": "Borlabs Cookie", "Präfix": "royals_"}
  }
Nur Python-Standardbibliothek (3.8+).
"""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

VERSION = "1.0.0"
HERE = os.path.dirname(os.path.abspath(__file__))
RULES_DIR = os.path.join(os.path.dirname(HERE), "rules")
CONFIG_NAME = ".web-guardrails.json"
SUPPRESS = "dsgvo-ok"

SCAN_EXT = {
    ".php", ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".astro",
    ".css", ".scss", ".sass", ".less", ".html", ".htm", ".twig", ".njk", ".json", ".svg",
}
SKIP_DIRS = {
    "vendor", "node_modules", ".git", ".claude", ".claude-plugin", "wp-admin", "wp-includes",
    "uploads", "languages", "dist-vendor", ".next", ".nuxt", ".svelte-kit", "coverage",
}
SKIP_SUFFIX = (".min.js", ".min.css", ".map", "package-lock.json", "composer.lock",
               "pnpm-lock.yaml", "yarn.lock")

SG = r"\$_(?:GET|POST|REQUEST|COOKIE)"

# id, level, pack, regex, hint
#   pack "common"    -> alle Webdateien
#   pack "php"       -> nur .php
#   pack "wordpress" -> nur wenn Stack "wordpress" aktiv ist
RULES = [
    # ---------- BLOCK: harte Verstöße, werden vor dem Schreiben verhindert ----------
    ("google_fonts_remote", "block", "common",
     r"fonts\.(?:googleapis|gstatic)\.com",
     "Google Fonts werden remote geladen (IP-Übertragung an Google, LG München I 3 O 17493/20). "
     "Schrift als WOFF2 lokal ablegen und per @font-face (bzw. theme.json fontFace / next/font local) einbinden."),
    ("hardcoded_live_secret", "block", "common",
     r"sk_live_[0-9A-Za-z]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{35}|ghp_[0-9A-Za-z]{30,}|xox[bp]-[0-9A-Za-z\-]{10,}",
     "Hartkodierter Live-Schlüssel. In Umgebungsvariable bzw. wp-config.php-Konstante auslagern, nie ins Repo."),
    ("superglobal_in_sql", "block", "php",
     r"(?:\$wpdb->\w+|->query|mysqli_query|->prepare)\s*\([^;]*" + SG,
     "Superglobal direkt in einer SQL-Abfrage (SQL-Injection). Prepared Statements mit Platzhaltern "
     "($wpdb->prepare) und vorher wp_unslash() + sanitize_*()."),
    ("superglobal_dangerous_sink", "block", "php",
     r"\b(?:eval|assert|unserialize|maybe_unserialize|extract|include|include_once|require|require_once)\s*\(?\s*" + SG,
     "Benutzereingabe in eval/unserialize/extract/include (Code-Ausführung, Object Injection, LFI). "
     "Nicht erlaubt. JSON + Whitelist verwenden."),
    ("superglobal_echo", "block", "php",
     r"(?:\b(?:echo|print)\s+|<\?=\s*)\$_(?:GET|POST|REQUEST|COOKIE|SERVER)",
     "Superglobal wird ungeescaped ausgegeben (reflektiertes XSS). esc_html()/esc_attr()/esc_url() bzw. htmlspecialchars()."),

    # ---------- WARN: Drittanbieter / DSGVO, werden nach dem Schreiben gemeldet ----------
    ("analytics_tracking", "warn", "common",
     r"googletagmanager\.com|google-analytics\.com|\bgtag\s*\(|connect\.facebook\.net|\bfbq\s*\(|"
     r"static\.hotjar\.com|clarity\.ms|snap\.licdn\.com|analytics\.tiktok\.com|static\.ads-twitter\.com",
     "Tracking/Analytics-Skript. Darf erst nach Einwilligung laden (Consent-Tool)."),
    ("video_embed", "warn", "common",
     r"youtube(?:-nocookie)?\.com/embed|youtu\.be/|player\.vimeo\.com|open\.spotify\.com/embed",
     "Video-/Audio-Embed. Nur als 2-Klick-Lösung mit lokalem Vorschaubild, auch bei youtube-nocookie."),
    ("maps_embed", "warn", "common",
     r"maps\.google\.|google\.[a-z.]+/maps|maps\.googleapis\.com|api\.mapbox\.com|tile\.openstreetmap\.org",
     "Karten-Embed lädt Drittserver. 2-Klick-Lösung oder lokal gehostetes Kartenbild."),
    ("social_embed", "warn", "common",
     r"platform\.(?:twitter|x)\.com|instagram\.com/embed|cdninstagram\.com|connect\.facebook\.net/[a-z_]+/sdk|"
     r"assets\.calendly\.com|embed\.typeform\.com",
     "Social-/Widget-Embed lädt Drittserver. Nur hinter Consent bzw. als einfacher Link."),
    ("captcha_remote", "warn", "common",
     r"google\.com/recaptcha|recaptcha/api\.js|gstatic\.com/recaptcha|hcaptcha\.com|challenges\.cloudflare\.com",
     "Remote-CAPTCHA überträgt Daten an Dritte. Consent nötig oder lokale Alternative (Honeypot, Zeitprüfung)."),
    ("cdn_library", "warn", "common",
     r"cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com|code\.jquery\.com|ajax\.googleapis\.com|"
     r"(?:stackpath|maxcdn)\.bootstrapcdn\.com|kit\.fontawesome\.com|use\.fontawesome\.com|use\.typekit\.net|p\.typekit\.net",
     "Bibliothek oder Schrift vom CDN. Lokal ausliefern (npm-Paket bundeln bzw. Datei ins Theme legen)."),
    ("external_script_tag", "warn", "common",
     r"<script[^>]+src\s*=\s*[\"']https?://",
     "Externes <script src>. Lokal ausliefern."),
    ("external_css_import", "warn", "common",
     r"@import\s+(?:url\()?\s*[\"']?https?://|<link[^>]+href\s*=\s*[\"']https?://[^\"']+\.css",
     "Externes Stylesheet. Lokal ausliefern."),
    ("external_font_src", "warn", "common",
     r"src\s*:\s*url\(\s*[\"']?https?://",
     "@font-face lädt Schrift von externer URL. WOFF2 lokal ablegen."),
    ("external_enqueue", "warn", "wordpress",
     r"wp_(?:enqueue|register)_(?:script|style)\s*\([^;]*[\"']https?://",
     "Enqueue mit externer URL. Datei lokal ablegen und get_theme_file_uri()/plugins_url() verwenden."),
    ("gravatar", "warn", "wordpress",
     r"gravatar\.com|\bget_avatar(?:_url)?\s*\(",
     "Gravatar überträgt einen Hash der E-Mail an Automattic. Deaktivieren oder lokal ersetzen."),
]

COMPILED = [(i, lvl, pack, re.compile(rx, re.I), hint) for i, lvl, pack, rx, hint in RULES]


# ----------------------------------------------------------------------------- helpers
def project_root(data=None):
    return os.environ.get("CLAUDE_PROJECT_DIR") or (data or {}).get("cwd") or os.getcwd()


def load_config(root):
    path = os.path.join(root, CONFIG_NAME)
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        return {}


def _head(path, n=4096):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(n)
    except OSError:
        return ""


def detect_stacks(root, cfg=None):
    cfg = cfg if cfg is not None else load_config(root)
    if isinstance(cfg.get("stacks"), list) and cfg["stacks"]:
        return sorted(set(cfg["stacks"]))
    stacks = set()
    root = os.path.abspath(root)
    base_depth = root.rstrip(os.sep).count(os.sep)
    for d, dirs, files in os.walk(root):
        depth = d.count(os.sep) - base_depth
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")] if depth < 3 else []
        names = set(files)
        if "wp-config.php" in names or "wp-content" in dirs or "theme.json" in names:
            stacks.add("wordpress")
        if "style.css" in names and "Theme Name:" in _head(os.path.join(d, "style.css")):
            stacks.add("wordpress")
        if depth <= 1:
            for fn in files:
                if fn.endswith(".php") and "Plugin Name:" in _head(os.path.join(d, fn), 2048):
                    stacks.add("wordpress")
                    break
        if "composer.json" in names:
            c = _head(os.path.join(d, "composer.json"), 20000)
            if re.search(r"wpackagist|johnpbloch/wordpress|roots/wordpress|roots/bedrock", c):
                stacks.add("wordpress")
        if "wordpress" in stacks:
            break
    return sorted(stacks)


def should_scan(path, cfg=None):
    if not path:
        return False
    norm = path.replace("\\", "/")
    parts = norm.split("/")
    skip = SKIP_DIRS | set((cfg or {}).get("skip_dirs", []))
    if any(p in skip for p in parts[:-1]):
        return False
    name = parts[-1].lower()
    if name.endswith(SKIP_SUFFIX):
        return False
    return os.path.splitext(name)[1] in SCAN_EXT


def applicable(path, stacks, cfg, levels):
    ext = os.path.splitext(path.lower())[1]
    disabled = set(cfg.get("disable_rules", []))
    out = []
    for rid, lvl, pack, rx, hint in COMPILED:
        if lvl not in levels or rid in disabled:
            continue
        if pack == "php" and ext != ".php":
            continue
        if pack == "wordpress" and "wordpress" not in stacks:
            continue
        out.append((rid, lvl, rx, hint))
    return out


def find(text, rules, cfg):
    allow = [h.lower() for h in cfg.get("allow_hosts", []) if h]
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if SUPPRESS in line:
            continue
        low = line.lower()
        if allow and any(h in low for h in allow):
            continue
        for rid, lvl, rx, hint in rules:
            m = rx.search(line)
            if m:
                hits.append((lineno, rid, lvl, m.group(0)[:80], hint))
    return hits


def new_content(tool_input):
    if "content" in tool_input:                       # Write
        return tool_input.get("content") or ""
    if "new_string" in tool_input:                    # Edit
        return tool_input.get("new_string") or ""
    if "edits" in tool_input:                         # MultiEdit
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    return ""


def read_file(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


# ----------------------------------------------------------------------------- modes
def mode_context():
    root = project_root()
    cfg = load_config(root)
    stacks = detect_stacks(root, cfg)
    parts = []
    for name in ["common"] + stacks:
        txt = read_file(os.path.join(RULES_DIR, f"{name}.md"))
        if txt:
            parts.append(txt.strip())
    ctx = cfg.get("context")
    if isinstance(ctx, dict) and ctx:
        parts.append("## Projektkontext (aus .web-guardrails.json)\n\n" +
                     "\n".join(f"- {k}: {v}" for k, v in ctx.items()))
    status = [f"web-guardrails {VERSION} ist aktiv. Erkannte Stacks: {', '.join(stacks) or 'keiner (nur allgemeine Regeln)'}."]
    if "wordpress" in stacks and not os.path.isfile(os.path.join(root, ".claude", "security-patterns.json")):
        status.append("Für dieses WordPress-Projekt wurde das Projekt-Setup noch nicht ausgeführt "
                      "(/web-guardrails:init legt Security-Patterns, CI und Git-Hook an).")
    parts.append("\n".join(status))
    print("\n\n".join(parts))
    return 0


def mode_pre(data):
    ti = data.get("tool_input") or {}
    path = ti.get("file_path", "")
    root = project_root(data)
    cfg = load_config(root)
    if not should_scan(path, cfg):
        return 0
    rules = applicable(path, detect_stacks(root, cfg), cfg, {"block"})
    hits = find(new_content(ti), rules, cfg)
    if not hits:
        return 0
    lines = [f"web-guardrails hat das Schreiben von {os.path.basename(path)} blockiert:"]
    for _, rid, _, snippet, hint in hits[:8]:
        lines.append(f"- [{rid}] `{snippet}`: {hint}")
    lines.append("Bitte korrigieren und erneut schreiben. Bewusste Ausnahme nur mit `dsgvo-ok: <Begründung>` in der Zeile.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "\n".join(lines),
    }}, ensure_ascii=False))
    return 0


def _seen_store(session_id):
    key = hashlib.sha1((session_id or "nosession").encode()).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), f"web-guardrails-{key}.json")


def mode_post(data):
    ti = data.get("tool_input") or {}
    path = ti.get("file_path", "")
    root = project_root(data)
    cfg = load_config(root)
    if not should_scan(path, cfg) or not os.path.isfile(path):
        return 0
    text = read_file(path)
    if text is None:
        return 0
    hits = find(text, applicable(path, detect_stacks(root, cfg), cfg, {"warn"}), cfg)
    if not hits:
        return 0
    store = _seen_store(data.get("session_id"))
    try:
        with open(store, encoding="utf-8") as f:
            seen = set(json.load(f))
    except (OSError, ValueError):
        seen = set()
    fresh = []
    for lineno, rid, lvl, snippet, hint in hits:
        k = f"{os.path.abspath(path)}|{rid}|{snippet}"
        if k not in seen:
            seen.add(k)
            fresh.append((lineno, rid, snippet, hint))
    try:
        with open(store, "w", encoding="utf-8") as f:
            json.dump(sorted(seen), f)
    except OSError:
        pass
    if not fresh:
        return 0
    rel = os.path.relpath(path, root) if os.path.isabs(path) else path
    out = [f"web-guardrails (DSGVO): Drittanbieter-Verbindungen in {rel}:"]
    for lineno, rid, snippet, hint in fresh[:12]:
        out.append(f"- Z.{lineno} [{rid}] `{snippet}`: {hint}")
    out.append("Beheben oder, falls bewusst consent-gesteuert, mit `dsgvo-ok: <Begründung>` markieren "
               "und in der Antwort unter 'Neue Drittanbieter' aufführen.")
    print("\n".join(out), file=sys.stderr)
    return 2


def _staged_files():
    try:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
                             capture_output=True, check=True).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.CalledProcessError):
        return []
    return [p for p in out.split("\0") if p]


def _staged_text(path):
    try:
        return subprocess.run(["git", "show", f":{path}"], capture_output=True, check=True
                              ).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.CalledProcessError):
        return None


def mode_scan(argv):
    flags = {a for a in argv if a.startswith("--")}
    paths = [a for a in argv if not a.startswith("--")]
    root = os.getcwd()
    cfg = load_config(root)
    stacks = detect_stacks(root, cfg)

    items = []  # (display_path, text)
    if "--staged" in flags:
        for p in _staged_files():
            if should_scan(p, cfg):
                t = _staged_text(p)
                if t is not None:
                    items.append((p, t))
    else:
        for target in paths or ["."]:
            if os.path.isfile(target):
                candidates = [target]
            else:
                candidates = []
                skip = SKIP_DIRS | set(cfg.get("skip_dirs", []))
                for d, dirs, fs in os.walk(target):
                    dirs[:] = sorted(x for x in dirs if x not in skip)
                    candidates += [os.path.join(d, x) for x in sorted(fs)]
            for fp in candidates:
                if should_scan(fp, cfg):
                    t = read_file(fp)
                    if t is not None:
                        items.append((fp, t))

    n_block = n_warn = 0
    for fp, text in items:
        for lineno, rid, lvl, snippet, hint in find(text, applicable(fp, stacks, cfg, {"block", "warn"}), cfg):
            tag = "BLOCK" if lvl == "block" else "WARN "
            print(f"{tag} {fp}:{lineno} [{rid}] {snippet}\n      -> {hint}")
            if "--github" in flags:
                kind = "error" if lvl == "block" else "warning"
                msg = f"[{rid}] {hint}".replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
                gh_path = fp[2:] if fp.startswith("./") else fp
                print(f"::{kind} file={gh_path},line={lineno},title=web-guardrails::{msg}")
            if lvl == "block":
                n_block += 1
            else:
                n_warn += 1
    print(f"\nweb-guardrails: {len(items)} Dateien geprüft, {n_block} BLOCK, {n_warn} WARN "
          f"(Stacks: {', '.join(stacks) or '-'})")
    if n_block or ("--strict" in flags and n_warn):
        return 1
    return 0


HOOK_MARK = "# web-guardrails pre-commit"


def mode_install_git_hook():
    try:
        hooks_dir = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], capture_output=True,
                                   check=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        print("Kein Git-Repository gefunden.", file=sys.stderr)
        return 1
    os.makedirs(hooks_dir, exist_ok=True)
    target_dir = os.path.join(hooks_dir, "web-guardrails")
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
    shutil.copytree(os.path.dirname(HERE), target_dir,
                    ignore=shutil.ignore_patterns("templates", "skills", "hooks", ".claude-plugin", "__pycache__"))
    script = (
        "#!/bin/sh\n"
        f"{HOOK_MARK} {VERSION}\n"
        'PY=$(command -v python3 || command -v python)\n'
        '[ -z "$PY" ] && { echo "web-guardrails: python3 nicht gefunden, Prüfung übersprungen" >&2; exit 0; }\n'
        '"$PY" "$(git rev-parse --git-path hooks)/web-guardrails/scripts/guard.py" scan --staged || {\n'
        '  echo "web-guardrails: Commit abgebrochen (BLOCK-Funde). Ausnahme: dsgvo-ok: <Begründung> oder git commit --no-verify" >&2\n'
        "  exit 1\n"
        "}\n"
    )
    hook = os.path.join(hooks_dir, "pre-commit")
    if os.path.isfile(hook) and HOOK_MARK not in (read_file(hook) or ""):
        hook = os.path.join(hooks_dir, "pre-commit.web-guardrails")
        print(f"Es existiert bereits ein eigener pre-commit-Hook. Neuer Hook liegt unter {hook}; "
              "bitte von dort aus dem bestehenden Hook aufrufen.")
    with open(hook, "w", encoding="utf-8") as f:
        f.write(script)
    os.chmod(hook, os.stat(hook).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"web-guardrails pre-commit-Hook installiert: {hook}")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "scan":
        return mode_scan(sys.argv[2:])
    if cmd == "context":
        return mode_context()
    if cmd == "stacks":
        root = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        print(" ".join(detect_stacks(root)) or "-")
        return 0
    if cmd == "install-git-hook":
        return mode_install_git_hook()
    if cmd == "--version":
        print(VERSION)
        return 0
    if cmd in ("pre", "post"):
        try:
            data = json.load(sys.stdin)
        except ValueError:
            return 0  # kaputter Input: Sitzung nie blockieren
        return mode_pre(data) if cmd == "pre" else mode_post(data)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
