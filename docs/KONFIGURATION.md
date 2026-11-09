# Konfiguration

[← Zurück zur README](../README.md)

## Projektdatei `.web-guardrails.json`

Liegt im Projektwurzelverzeichnis und ist optional. Ungültiges JSON oder ein Nicht-Objekt wird ignoriert (leere Konfiguration).

| Schlüssel | Typ | Wirkung |
|---|---|---|
| `stacks` | Liste | überschreibt die Auto-Erkennung (derzeit unterstützt: `wordpress`) |
| `allow_hosts` | Liste | Zeilen, die einen dieser Hosts enthalten, werden nicht gemeldet |
| `disable_rules` | Liste | Regel-IDs, die deaktiviert werden |
| `skip_dirs` | Liste | zusätzliche Verzeichnisnamen, die übersprungen werden |
| `context` | Objekt | Schlüssel/Wert-Paare, die Claude beim Sitzungsstart als Projektkontext erhält |

```json
{
  "stacks": ["wordpress"],
  "allow_hosts": ["cdn.meinverein.de"],
  "disable_rules": ["gravatar"],
  "skip_dirs": ["legacy"],
  "context": { "Consent-Tool": "Borlabs Cookie", "Präfix": "royals_" }
}
```

## Zeilen-Ausnahme

Kommentar `dsgvo-ok: <Begründung>` in derselben Zeile unterdrückt alle Funde dieser Zeile.

## Umgebungsvariablen

| Variable | Verwendung |
|---|---|
| `CLAUDE_PROJECT_DIR` | Projektwurzel für Hooks (Fallback: `cwd` aus Payload, dann aktuelles Verzeichnis) |
| `WG_PATH` | Action-intern: Wert des Inputs `path` |
| `WG_STRICT` | Action-intern: Wert des Inputs `strict` |
| `WG_SCRIPT` | Action-intern: Pfad zu `guard.py` |

Hinweis: `scan` nutzt das aktuelle Arbeitsverzeichnis als Projektwurzel für `.web-guardrails.json`.

## GitHub-Action-Inputs

| Input | Standard | Beschreibung |
|---|---|---|
| `path` | `.` | zu prüfender Pfad relativ zum Repository |
| `strict` | `false` | `true`: auch WARN-Funde lassen den Check scheitern |

## Regeln

| ID | Stufe | Pack |
|---|---|---|
| `google_fonts_remote` | BLOCK | common |
| `hardcoded_live_secret` | BLOCK | common |
| `superglobal_in_sql` | BLOCK | php |
| `superglobal_dangerous_sink` | BLOCK | php |
| `superglobal_echo` | BLOCK | php |
| `analytics_tracking` | WARN | common |
| `video_embed` | WARN | common |
| `maps_embed` | WARN | common |
| `social_embed` | WARN | common |
| `captcha_remote` | WARN | common |
| `cdn_library` | WARN | common |
| `external_script_tag` | WARN | common |
| `external_css_import` | WARN | common |
| `external_font_src` | WARN | common |
| `external_enqueue` | WARN | wordpress |
| `gravatar` | WARN | wordpress |

## Geprüfte Dateien

Erweiterungen: `.php .js .mjs .cjs .ts .jsx .tsx .vue .svelte .astro .css .scss .sass .less .html .htm .twig .njk .json .svg`.

Standardmäßig übersprungene Verzeichnisse: `vendor`, `node_modules`, `.git`, `.claude`, `.claude-plugin`, `wp-admin`, `wp-includes`, `uploads`, `languages`, `dist-vendor`, `.next`, `.nuxt`, `.svelte-kit`, `coverage`. Übersprungene Dateien: `*.min.js`, `*.min.css`, `*.map`, `package-lock.json`, `composer.lock`, `pnpm-lock.yaml`, `yarn.lock`.

## Hooks

| Hook | Befehl | Verhalten |
|---|---|---|
| SessionStart | `guard.py context` | gibt Regeln und Projektkontext aus |
| PreToolUse (Write/Edit/MultiEdit) | `guard.py pre` | `deny` bei BLOCK-Funden |
| PostToolUse | `guard.py post` | Exit 2 + stderr bei neuen WARN-Funden |

(Konkrete Zuordnung in `hooks/hooks.json` – Inhalt nicht eingesehen, aus Skript-Doku abgeleitet.)
