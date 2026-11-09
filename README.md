# web-guardrails

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white) ![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-green)

DSGVO- und Sicherheitsregeln für Webprojekte, die beim Vibe Coding mit Claude Code automatisch greifen – plus derselbe Check als Git-pre-commit-Hook und GitHub Action. Unterstützter Stack: **WordPress** (allgemeine Regeln gelten für jedes Webprojekt, weitere Stacks folgen).

## Features

| Schicht | Wann | Was |
|---|---|---|
| **Regeln laden** | Sitzungsstart, nach `/clear` und Kompaktierung | Claude bekommt die Projektkonventionen (DSGVO, Sicherheit, Lizenzen, Rechtstexte), passend zum erkannten Stack |
| **Blockieren** | vor jedem Write/Edit von Claude | Google Fonts remote, Live-API-Keys, Superglobals in SQL / `echo` / `unserialize` / `include` |
| **Melden** | nach jedem Write/Edit von Claude | Tracking, YouTube/Vimeo/Maps/Social-Embeds, reCAPTCHA, CDNs, externe Skripte/Styles/Fonts, Gravatar |
| **Git-pre-commit** | bei jedem Commit | blockiert BLOCK-Funde im gestagten Inhalt |
| **GitHub Action** | bei Push/PR | Funde als Annotations im PR |
| `/web-guardrails:init` | einmal pro Projekt | Projekt-Settings, Security-Patterns für das `security-guidance`-Plugin, CI, Git-Hook, Lizenzliste, erster Audit |
| `/web-guardrails:dsgvo-check` | vor dem Livegang | misst im Browser, was vor/nach dem Consent geladen wird |

## Tech-Stack

- Python 3.8+ (nur Standardbibliothek) – `plugins/web-guardrails/scripts/guard.py`
- Claude-Code-Plugin (Hooks, Skills, Regeldateien als Markdown)
- GitHub Action (Composite) und pre-commit-Framework
- Tests mit `unittest`

## Schnellstart

**Voraussetzungen:** Claude Code ab 2.1.144, `python3` (3.8+) im PATH. Unter Windows muss `python3` aufrufbar sein (z. B. über Python-App-Aliase oder Git Bash).

**Installation** in Claude Code:

```
/plugin marketplace add Infactionfreddy/web-guardrails
/plugin install web-guardrails@infactionfreddy-plugins
/plugin install security-guidance@claude-plugins-official
```

**Start:** Im Projekt einmal `/web-guardrails:init` ausführen.

### Ohne Claude Code

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Infactionfreddy/web-guardrails
    rev: v1.0.0
    hooks:
      - id: web-guardrails
```

```yaml
# .github/workflows/web-guardrails.yml (Schritte)
- uses: actions/checkout@v4
- uses: Infactionfreddy/web-guardrails@v1
  with:
    path: .
    strict: "false"
```

Manuell: `python3 plugins/web-guardrails/scripts/guard.py scan <pfad>` (Exit 1 bei BLOCK-Funden).

## Konfiguration

Umgebungsvariablen werden nur an wenigen Stellen verwendet; die Projektkonfiguration erfolgt über `.web-guardrails.json`.

| Variable | Bedeutung |
|---|---|
| `CLAUDE_PROJECT_DIR` | Projektwurzel (von Claude Code gesetzt, Fallback: `cwd` aus Hook-Payload bzw. aktuelles Verzeichnis) |
| `WG_PATH`, `WG_STRICT`, `WG_SCRIPT` | interne Variablen der GitHub Action (aus den Inputs `path`/`strict` abgeleitet) |

Beispiel `.web-guardrails.json`:

```json
{
  "stacks": ["wordpress"],
  "allow_hosts": ["cdn.meinverein.de"],
  "disable_rules": ["gravatar"],
  "skip_dirs": ["legacy"],
  "context": { "Consent-Tool": "Borlabs Cookie", "Präfix": "royals_" }
}
```

Eine einzelne, bewusst consent-gesteuerte Zeile wird mit dem Kommentar `dsgvo-ok: <Begründung>` ausgenommen. Details: [docs/KONFIGURATION.md](docs/KONFIGURATION.md).

## Regeln

| Regel | Stufe | Gilt für |
|---|---|---|
| `google_fonts_remote`, `hardcoded_live_secret` | BLOCK | alle Webdateien |
| `superglobal_in_sql`, `superglobal_dangerous_sink`, `superglobal_echo` | BLOCK | `.php` |
| `analytics_tracking`, `video_embed`, `maps_embed`, `social_embed`, `captcha_remote`, `cdn_library`, `external_script_tag`, `external_css_import`, `external_font_src` | WARN | alle Webdateien |
| `external_enqueue`, `gravatar` | WARN | WordPress |

Ausgenommen sind `vendor/`, `node_modules/`, `wp-admin/`, `wp-includes/`, `uploads/`, minifizierte Dateien und Lockfiles.

## Projektstruktur

```
.
├── action.yml                      # GitHub Action (Composite)
├── LICENSE
├── plugins/web-guardrails/
│   ├── hooks/hooks.json            # Claude-Code-Hooks
│   ├── rules/                      # common.md, wordpress.md (Kontext für Claude)
│   ├── scripts/guard.py            # Kern: Hooks, Scan, Git-Hook-Installer
│   ├── skills/                     # init, dsgvo-check
│   └── templates/                  # Vorlagen für /web-guardrails:init
└── tests/                          # unittest-Suite und Fixtures
```

## Grenzen

- Die Prüfung ist zeilenbasiert und heuristisch. Sie ersetzt weder PHPCS mit WordPress-Standard noch den Browser-Check der laufenden Seite noch rechtliche Beratung.
- Was Plugins oder Page-Builder zur Laufzeit nachladen, sieht nur `/web-guardrails:dsgvo-check`.
- Impressum und Datenschutzerklärung erzeugt das Plugin bewusst nicht.

## Entwicklung

```bash
python3 -m unittest discover -s tests -v
claude plugin validate ./plugins/web-guardrails
claude plugin validate .
```

Neuen Stack hinzufügen: Erkennung in `detect_stacks()`, Regeln mit `pack="<stack>"` in `RULES`, Konventionen in `plugins/web-guardrails/rules/<stack>.md`.

## Dokumentation

- [Architektur](docs/ARCHITEKTUR.md)
- [Installation](docs/INSTALLATION.md)
- [Konfiguration](docs/KONFIGURATION.md)
- [Entwicklung](docs/ENTWICKLUNG.md)
- [API / CLI-Referenz](docs/API.md)

## Lizenz

MIT – siehe [LICENSE](LICENSE).
