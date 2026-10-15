# web-guardrails

DSGVO- und Sicherheitsregeln für Webprojekte, die beim Vibe Coding mit Claude Code automatisch greifen,
plus derselbe Check als Git-pre-commit-Hook und GitHub Action. Unterstützter Stack: **WordPress**
(allgemeine Regeln gelten für jedes Webprojekt, weitere Stacks folgen).

## Was es tut

| Schicht | Wann | Was |
|---|---|---|
| **Regeln laden** | Sitzungsstart, nach `/clear` und Kompaktierung | Claude bekommt die Projektkonventionen (DSGVO, Sicherheit, Lizenzen, Rechtstexte), passend zum erkannten Stack |
| **Blockieren** | vor jedem Write/Edit von Claude | Google Fonts remote, Live-API-Keys, Superglobals in SQL / `echo` / `unserialize` / `include` |
| **Melden** | nach jedem Write/Edit von Claude | Tracking, YouTube/Vimeo/Maps/Social-Embeds, reCAPTCHA, CDNs, externe Skripte/Styles/Fonts, Gravatar |
| **Git-pre-commit** | bei jedem Commit, auch manuell oder aus Cursor/Lovable | blockiert BLOCK-Funde im gestagten Inhalt |
| **GitHub Action** | bei Push/PR | Funde als Annotations im PR |
| `/web-guardrails:init` | einmal pro Projekt | Projekt-Settings fürs Team, Security-Patterns für das offizielle `security-guidance`-Plugin, CI, Git-Hook, Lizenzliste, erster Audit |
| `/web-guardrails:dsgvo-check` | vor dem Livegang | misst im Browser, was vor/nach dem Consent geladen wird |

## Installation

In Claude Code:

```
/plugin marketplace add Infactionfreddy/web-guardrails
/plugin install web-guardrails@infactionfreddy-plugins
/plugin install security-guidance@claude-plugins-official
```

Dann im Projekt einmal `/web-guardrails:init` ausführen.

Voraussetzungen: Claude Code ab 2.1.144, `python3` (3.8+) im PATH. Unter Windows muss `python3` aufrufbar sein
(z. B. über die Python-App-Aliase oder Git Bash).

### Ohne Claude Code

**pre-commit-Framework** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/Infactionfreddy/web-guardrails
    rev: v1.0.0
    hooks:
      - id: web-guardrails
```

**GitHub Action** (`.github/workflows/web-guardrails.yml`):

```yaml
- uses: actions/checkout@v4
- uses: Infactionfreddy/web-guardrails@v1
  with:
    path: .
    strict: "false"
```

**Manuell:** `python3 plugins/web-guardrails/scripts/guard.py scan <pfad>` (Exit 1 bei BLOCK-Funden).

## Projekt-Konfiguration

Optional `.web-guardrails.json` im Projektwurzelverzeichnis:

```json
{
  "stacks": ["wordpress"],
  "allow_hosts": ["cdn.meinverein.de"],
  "disable_rules": ["gravatar"],
  "skip_dirs": ["legacy"],
  "context": { "Consent-Tool": "Borlabs Cookie", "Präfix": "royals_" }
}
```

- `stacks` überschreibt die Auto-Erkennung (WordPress wird über `wp-config.php`, `wp-content/`, `theme.json`,
  `Theme Name:` in `style.css`, `Plugin Name:`-Header oder Composer-Pakete erkannt).
- `context` wird Claude bei Sitzungsbeginn als Projektkontext mitgegeben.

Eine einzelne, bewusst consent-gesteuerte Zeile wird mit dem Kommentar `dsgvo-ok: <Begründung>` ausgenommen.

## Regeln

| Regel | Stufe | Gilt für |
|---|---|---|
| `google_fonts_remote` | BLOCK | alle Webdateien |
| `hardcoded_live_secret` | BLOCK | alle Webdateien |
| `superglobal_in_sql`, `superglobal_dangerous_sink`, `superglobal_echo` | BLOCK | `.php` |
| `analytics_tracking`, `video_embed`, `maps_embed`, `social_embed`, `captcha_remote`, `cdn_library`, `external_script_tag`, `external_css_import`, `external_font_src` | WARN | alle Webdateien |
| `external_enqueue`, `gravatar` | WARN | WordPress |

Ausgenommen sind `vendor/`, `node_modules/`, `wp-admin/`, `wp-includes/`, `uploads/`, minifizierte Dateien und Lockfiles.

## Grenzen

- Die Prüfung ist zeilenbasiert und heuristisch. Sie ersetzt weder PHPCS mit WordPress-Standard noch den
  Browser-Check der laufenden Seite noch rechtliche Beratung.
- Was Plugins oder Page-Builder zur Laufzeit nachladen, sieht nur `/web-guardrails:dsgvo-check`.
- Impressum und Datenschutzerklärung erzeugt das Plugin bewusst nicht.

## Entwicklung

```bash
python3 -m unittest discover -s tests -v
claude plugin validate ./plugins/web-guardrails
claude plugin validate .
```

Neuen Stack hinzufügen: Erkennung in `detect_stacks()`, Regeln mit `pack="<stack>"` in `RULES`,
Konventionen in `plugins/web-guardrails/rules/<stack>.md`.

## Lizenz

MIT
