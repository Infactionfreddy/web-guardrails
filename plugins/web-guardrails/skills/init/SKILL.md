---
name: init
description: Richtet web-guardrails einmalig im aktuellen Projekt ein (Projekt-Settings für Team und Cloud, Security-Patterns, CI-Workflow, Git-pre-commit-Hook, Lizenzliste) und macht einen ersten Audit. Nur auf ausdrücklichen Wunsch ausführen.
disable-model-invocation: true
---

# web-guardrails: Projekt einrichten

Plugin-Verzeichnis: `${CLAUDE_PLUGIN_ROOT}`
Engine: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py"`

Arbeite die Schritte der Reihe nach ab. Bestehende Dateien werden **nie überschrieben**, sondern zusammengeführt.
Zeige vor dem Schreiben jeweils kurz, was du anlegst oder änderst.

## 1. Stack und Kontext

1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" stacks .` ausführen und das Ergebnis nennen.
2. Mit einer Frage (AskUserQuestion, falls verfügbar) klären:
   - Welches Consent-Tool ist im Einsatz (z. B. Borlabs Cookie, Complianz, Real Cookie Banner, keins)?
   - Bei WordPress: Präfix und Text-Domain.
   - Soll CI (GitHub Action) und/oder ein lokaler Git-pre-commit-Hook eingerichtet werden?
3. `.web-guardrails.json` im Projektwurzelverzeichnis anlegen bzw. ergänzen:
   ```json
   {
     "stacks": ["<erkannte Stacks>"],
     "allow_hosts": [],
     "disable_rules": [],
     "context": { "Consent-Tool": "<Antwort>", "Präfix": "<Antwort>", "Text-Domain": "<Antwort>" }
   }
   ```
   `stacks` nur setzen, wenn die Erkennung falsch lag. Sonst weglassen, damit die Auto-Erkennung greift.

## 2. Projekt-Settings (damit Team und Cloud-Sessions das Plugin automatisch bekommen)

In `.claude/settings.json` folgende Schlüssel ergänzen (vorhandene Schlüssel erhalten, JSON gültig halten):

```json
{
  "extraKnownMarketplaces": {
    "infactionfreddy-plugins": {
      "source": { "source": "github", "repo": "Infactionfreddy/web-guardrails" }
    }
  },
  "enabledPlugins": {
    "web-guardrails@infactionfreddy-plugins": true,
    "security-guidance@claude-plugins-official": true
  }
}
```

## 3. Stack-spezifische Dateien

Nur wenn der Stack `wordpress` aktiv ist:

- `.claude/security-patterns.json`: fehlt die Datei, `${CLAUDE_PLUGIN_ROOT}/templates/security-patterns.wordpress.json`
  kopieren. Existiert sie, die Regeln aus der Vorlage ergänzen, deren `rule_name` noch fehlt (maximal 50 Regeln insgesamt).
- `.claude/claude-security-guidance.md`: fehlt sie, `${CLAUDE_PLUGIN_ROOT}/templates/claude-security-guidance.wordpress.md`
  kopieren. Existiert sie, den Inhalt der Vorlage unter einer Überschrift "web-guardrails (WordPress)" anhängen.
  Gesamtgröße unter 8 KB halten.

## 4. Lizenzliste

Fehlt `THIRD-PARTY-LICENSES.md`, `${CLAUDE_PLUGIN_ROOT}/templates/THIRD-PARTY-LICENSES.md` kopieren. Danach gebündelte
Bibliotheken und Schriften im Projekt suchen (z. B. `assets/`, `vendor/`-Verzeichnisse im Theme, `package.json`-Abhängigkeiten,
`@font-face`) und gefundene Einträge mit Lizenz eintragen. Unklare Lizenzen als "zu prüfen" markieren, nicht raten.

## 5. CI und Git-Hook (nur wenn gewünscht)

- **GitHub Action:** `${CLAUDE_PLUGIN_ROOT}/templates/github-workflow.yml` nach `.github/workflows/web-guardrails.yml`
  kopieren, falls die Datei noch nicht existiert.
- **Git-pre-commit-Hook:**
  - Nutzt das Projekt bereits das pre-commit-Framework (`.pre-commit-config.yaml` vorhanden), den Eintrag aus
    `${CLAUDE_PLUGIN_ROOT}/templates/pre-commit-config.yaml` dort unter `repos:` ergänzen.
  - Sonst `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" install-git-hook` im Projektverzeichnis ausführen.
    Das installiert einen eigenständigen Hook unter `.git/hooks/`, der nur gestagte Inhalte prüft.

## 6. Erster Audit

`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" scan .` ausführen. Ergebnis zusammenfassen:
Anzahl BLOCK und WARN, gruppiert nach Regel, mit den wichtigsten Fundstellen. **Nichts automatisch korrigieren.**
Am Ende anbieten, die BLOCK-Funde zu beheben, und darauf hinweisen, dass `/web-guardrails:dsgvo-check` die laufende
Seite im Browser prüft.
