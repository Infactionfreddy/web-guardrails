# API / CLI-Referenz

[← Zurück zur README](../README.md)

Das Projekt hat keine HTTP-API; die Schnittstellen sind die CLI von `guard.py`, die Hook-Protokolle und die GitHub Action.

## CLI

```
python3 plugins/web-guardrails/scripts/guard.py <befehl> [optionen]
```

| Befehl | Beschreibung | Exit-Code |
|---|---|---|
| `context` | gibt Regeln (common + erkannte Stacks) und Projektkontext auf stdout aus | 0 |
| `pre` | PreToolUse-Hook, liest JSON von stdin | 0 (Verbot über JSON-Ausgabe) |
| `post` | PostToolUse-Hook, liest JSON von stdin | 2 bei neuen WARN-Funden, sonst 0 |
| `scan [opts] [pfade]` | Audit von Dateien/Ordnern (Standard: `.`) | 1 bei BLOCK (bzw. WARN mit `--strict`), sonst 0 |
| `stacks [pfad]` | gibt erkannte Stacks aus (`-` wenn keiner) | 0 |
| `install-git-hook` | installiert pre-commit-Hook im aktuellen Repo | 1 ohne Git-Repo |
| `--version` | gibt die Version aus | 0 |

### Optionen für `scan`

| Option | Wirkung |
|---|---|
| `--staged` | prüft nur gestagte Inhalte (Index) |
| `--github` | gibt zusätzlich `::error`/`::warning`-Annotations aus |
| `--strict` | WARN-Funde lassen den Scan scheitern |

Ausgabeformat: `BLOCK|WARN <datei>:<zeile> [<regel>] <treffer>` gefolgt von `-> <hinweis>` und einer Zusammenfassung `N Dateien geprüft, X BLOCK, Y WARN`.

## Hook-Protokoll

Eingabe (stdin, JSON): `tool_name`, `tool_input` (`file_path`, `content` | `new_string` | `edits[].new_string`), `session_id`, `cwd`.

Ausgabe von `pre` bei Verstoß:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}
```

`post` schreibt Meldungen auf stderr und beendet sich mit Exit 2.

## Skills

| Skill | Zweck |
|---|---|
| `/web-guardrails:init` | Projekt-Setup (einmalig) |
| `/web-guardrails:dsgvo-check` | Browser-Messung vor/nach Consent |

## GitHub Action

`Infactionfreddy/web-guardrails@v1` mit Inputs `path` (Standard `.`) und `strict` (Standard `false`). Keine Outputs.

## Interne Funktionen (guard.py)

| Funktion | Zweck |
|---|---|
| `detect_stacks(root, cfg)` | Liste erkannter Stacks |
| `should_scan(path, cfg)` | Dateifilter nach Erweiterung/Verzeichnis |
| `applicable(path, stacks, cfg, levels)` | passende Regeln |
| `find(text, rules, cfg)` | Treffer als `(zeile, regel, stufe, snippet, hinweis)` |
