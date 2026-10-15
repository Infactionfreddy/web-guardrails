---
name: dsgvo-check
description: Prüft eine laufende Website (z. B. WordPress) im Browser darauf, welche Drittanbieter-Verbindungen, Cookies und localStorage-Einträge VOR und NACH der Cookie-Einwilligung entstehen, plus Pflichtlinks und Security-Header. Verwenden bei "DSGVO-Check", "Consent prüfen", "was lädt die Seite vor dem Cookie-Banner", vor jedem Livegang.
---

# DSGVO-Laufzeit-Check

Ziel: belegen, was ein Besucher-Browser tatsächlich anfragt. Der Code-Scan (`wp-guard.py`) sieht
nur den Quelltext. Plugins, Page-Builder und nachgeladene Skripte zeigen sich erst zur Laufzeit.

Eingabe: Start-URL (z. B. `https://staging.example.de` oder `http://localhost:8080`). Fehlt sie, frag danach.

## Ablauf

1. **Sauberer Zustand.** Ein Browser-Kontext ohne gespeicherte Einwilligung ist Pflicht. Im
   Browser-Tool vorher die Website-Daten der Domain löschen oder einen frischen Kontext nutzen
   (Playwright-/DevTools-MCP: neuer Context). Sonst ist das Ergebnis wertlos, weil der alte Consent greift.

2. **Phase A: vor jeder Interaktion.** Startseite laden, 5 s warten, **nichts anklicken**.
   - Alle Netzwerk-Requests erfassen (Network-Tool des Browsers).
   - Per JavaScript erfassen: `document.cookie`, `Object.keys(localStorage)`,
     `Object.keys(sessionStorage)`.
   - Jeden Request nach Host einordnen: erstanbietig (gleiche Domain/Subdomain) oder Drittanbieter.

3. **Phase B: "Ablehnen" / "Nur notwendige".** Im Banner die ablehnende Option wählen, neu laden,
   Messung wie in A wiederholen. Prüfen, ob die Ablehnen-Option auf der ersten Ebene gleichwertig
   zur Zustimmen-Option erreichbar ist.

4. **Phase C: "Alle akzeptieren".** Daten löschen, neu laden, zustimmen, Messung wiederholen.
   Erwartung: Drittanbieter erscheinen erst jetzt.

5. **Unterseiten.** A und B zusätzlich für Kontaktseite, eine Seite mit Video/Karte (falls vorhanden)
   und eine Beitragsseite mit Kommentaren (Gravatar!) durchführen.

6. **Pflichtangaben.** Auf jeder geprüften Seite: Links "Impressum" und "Datenschutz" im Footer
   vorhanden und erreichbar, auch aus dem Cookie-Banner heraus.

7. **Security-Header** der Startseite per HTTP-HEAD prüfen: `Strict-Transport-Security`,
   `Content-Security-Policy` (oder mindestens `X-Content-Type-Options: nosniff`, `Referrer-Policy`,
   `X-Frame-Options`/`frame-ancestors`), keine `X-Powered-By`-Versionsangabe.

## Ergebnis

Gib eine kompakte Tabelle pro Phase aus:

| Host | Typ (Font/Skript/Embed/Tracking/CDN) | Ausgelöst durch (Plugin/Theme/Datei, wenn erkennbar) | Bewertung |

Bewertung:
- **Kritisch**: Drittanbieter-Request oder nicht notwendiges Cookie/Storage in Phase A oder B.
- **Hinweis**: Drittanbieter nur in Phase C (prüfen, ob in der Datenschutzerklärung genannt).
- **OK**: nur erstanbietige Requests bzw. technisch notwendige Cookies (Session, Consent-Status).

Danach für jeden kritischen Fund die konkrete Ursache im Code suchen (Theme, Plugin, Builder-Einstellung)
und einen Fix vorschlagen, z. B. Font lokal hosten, Embed über das Consent-Tool blockieren oder
CDN-Asset lokal ablegen. Keine Rechtstexte formulieren, nur auf fehlende Angaben hinweisen.
