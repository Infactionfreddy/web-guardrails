# Entwicklung

[← Zurück zur README](../README.md)

## Lokale Umgebung

```bash
git clone https://github.com/Infactionfreddy/web-guardrails.git
cd web-guardrails
python3 --version   # 3.8+
```

Es gibt keine Abhängigkeiten außerhalb der Python-Standardbibliothek. Für Plugin-Validierung wird die Claude-Code-CLI benötigt.

## Code-Struktur

| Bereich | Beschreibung |
|---|---|
| `RULES` / `COMPILED` | Regelliste und vorkompilierte Regexe in `guard.py` |
| `detect_stacks()` | Stack-Erkennung |
| `should_scan()`, `applicable()`, `find()` | Dateifilter, Regelauswahl, zeilenweise Suche |
| `mode_context/pre/post/scan` | Einstiegspunkte der Befehle |
| `mode_install_git_hook()` | Installation des pre-commit-Hooks |
| `rules/*.md` | Texte für den Claude-Kontext |

## Tests

```bash
python3 -m unittest discover -s tests -v
claude plugin validate ./plugins/web-guardrails
claude plugin validate .
```

Die Tests starten `guard.py` als Subprozess in temporären Verzeichnissen und decken Stack-Erkennung, Kontextausgabe, Pre-/Post-Hook, Scan (inkl. GitHub-Annotations und `--strict`) sowie den Git-Hook ab. Der Git-Test wird ohne installiertes `git` übersprungen. Nicht automatisiert getestet: Skills, Templates, `action.yml`.

## Neue Regel hinzufügen

1. Tupel in `RULES` ergänzen (ID, `block`/`warn`, Pack, Regex, Hinweis).
2. Test in `tests/test_guard.py` ergänzen (positiver und negativer Fall).
3. Regeltabelle in README und `docs/KONFIGURATION.md` aktualisieren.

## Neuen Stack hinzufügen

1. Erkennung in `detect_stacks()` ergänzen.
2. Regeln mit `pack="<stack>"` in `RULES` anlegen und in `applicable()` berücksichtigen.
3. Konventionen in `plugins/web-guardrails/rules/<stack>.md` schreiben (Kontext ist auf 10.000 Zeichen begrenzt, siehe Test).

## Coding-Standards

- Nur Standardbibliothek, Kompatibilität mit Python 3.8.
- Hooks dürfen eine Sitzung bei Fehlern nie blockieren (fail-open).
- Hinweistexte auf Deutsch, mit konkreter Lösung.
- Offizielle Linter-Konfiguration ist im Repo nicht vorhanden (Annahme: keine).

## Release-Ablauf (Annahme)

1. `VERSION` in `guard.py` anheben (ggf. Plugin-Manifest, nicht eingesehen).
2. Tests und `claude plugin validate` ausführen.
3. Git-Tag `vX.Y.Z` setzen sowie den Major-Tag (`v1`) für die GitHub Action nachziehen.
4. In Doku-Beispielen `rev:` aktualisieren.
