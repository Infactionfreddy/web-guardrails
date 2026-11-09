# Installation

[← Zurück zur README](../README.md)

## Voraussetzungen

- Claude Code ab 2.1.144 (nur für die Plugin-Nutzung)
- `python3` (3.8+) im PATH; unter Windows z. B. über Python-App-Aliase oder Git Bash
- Git (für pre-commit-Hook)
- Keine weiteren Python-Pakete nötig

## Variante A: Claude-Code-Plugin

1. Marketplace hinzufügen:
   ```
   /plugin marketplace add Infactionfreddy/web-guardrails
   ```
2. Plugin installieren:
   ```
   /plugin install web-guardrails@infactionfreddy-plugins
   /plugin install security-guidance@claude-plugins-official
   ```
3. Im Projekt einmal `/web-guardrails:init` ausführen (Settings, Security-Patterns, CI, Git-Hook, Lizenzliste, erster Audit).

## Variante B: pre-commit-Framework

```yaml
repos:
  - repo: https://github.com/Infactionfreddy/web-guardrails
    rev: v1.0.0
    hooks:
      - id: web-guardrails
```

Danach `pre-commit install` ausführen.

## Variante C: Eigener Git-Hook

```bash
cd mein-projekt
python3 /pfad/zu/web-guardrails/plugins/web-guardrails/scripts/guard.py install-git-hook
```

## Variante D: GitHub Action

```yaml
- uses: actions/checkout@v4
- uses: Infactionfreddy/web-guardrails@v1
  with:
    path: .
    strict: "false"
```

## Variante E: Manuell

```bash
python3 plugins/web-guardrails/scripts/guard.py scan <pfad>
```

## Installation prüfen

```bash
python3 plugins/web-guardrails/scripts/guard.py --version
python3 plugins/web-guardrails/scripts/guard.py stacks .
```

## Update

- Plugin: über den Plugin-Manager von Claude Code aktualisieren (Annahme: `/plugin`-Menü).
- pre-commit-Framework: `rev` anheben bzw. `pre-commit autoupdate`.
- GitHub Action: Tag in `uses:` anpassen.
- Eigener Git-Hook: `install-git-hook` erneut ausführen (das Verzeichnis `hooks/web-guardrails` wird ersetzt).

## Deinstallation

- Plugin: `/plugin` Verwaltung bzw. Plugin entfernen (Annahme).
- Git-Hook: `.git/hooks/pre-commit` (sofern von web-guardrails erzeugt, erkennbar am Kommentar `# web-guardrails pre-commit`) und das Verzeichnis `.git/hooks/web-guardrails` löschen.
- Projektdateien, die `/web-guardrails:init` angelegt hat (z. B. Workflow, `.claude/security-patterns.json`, `.web-guardrails.json`), manuell entfernen.
- Temporäre Merker-Dateien `web-guardrails-*.json` im Temp-Verzeichnis sind unkritisch.
