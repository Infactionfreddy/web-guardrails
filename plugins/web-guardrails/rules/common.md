# Projektkonventionen: Datenschutz und Sicherheit (web-guardrails)

Diese Website wird in Deutschland betrieben. Besucher sind in der EU, es gelten DSGVO und TDDDG.
Die folgenden Konventionen gelten für jede Code-Änderung in diesem Projekt. Ist eine Anforderung nur unter
Verletzung einer Konvention umsetzbar, wird sie nicht umgesetzt, sondern das Problem benannt und eine Alternative vorgeschlagen.

## Datenschutz

- Beim Seitenaufruf entsteht ohne Einwilligung keine Verbindung zu Drittservern. Schriften, Icons sowie
  JS- und CSS-Bibliotheken werden lokal ausgeliefert. CDNs (jsDelivr, cdnjs, unpkg, Google Hosted Libraries,
  Font Awesome Kit, Adobe Fonts) werden nicht verwendet.
- Schriften liegen als WOFF2 im Projekt und werden per @font-face eingebunden, nie über fonts.googleapis.com.
  Die Lizenz muss Webfont-Nutzung erlauben (z. B. OFL).
- Embeds (YouTube, Vimeo, Google Maps, Instagram, X, Spotify, Kalender- oder Ticket-Widgets) laden erst nach
  Einwilligung (2-Klick-Lösung oder Blockierung durch das Consent-Tool, mit lokalem Vorschaubild).
  youtube-nocookie.com allein genügt nicht.
- Tracking und Analytics laden nur nach Einwilligung. Bevorzugt wird cookielose, selbst gehostete Statistik.
- Cookies und localStorage/sessionStorage werden ohne Einwilligung nur für technisch zwingend nötige Zwecke
  genutzt (§ 25 TDDDG).
- Formulare erheben nur notwendige Felder. Personenbezogene Daten werden nur gespeichert, wenn nötig, dann mit
  Zweck, Löschfrist und automatischer Löschung. IP-Adressen werden nicht gespeichert oder geloggt.
- Kommt durch eine Änderung ein neuer externer Dienst oder eine neue Domain hinzu, nennt die Antwort ihn am Ende
  unter der Überschrift "Neue Drittanbieter" mit Zweck, damit die Datenschutzerklärung angepasst werden kann.
- Bewusst consent-gesteuerte Einbindungen tragen in derselben Zeile den Kommentar `dsgvo-ok: <Begründung>`.

## Sicherheit

- Eingaben werden validiert und gesäubert, Ausgaben kontextgerecht escaped (HTML, Attribut, URL, JS).
- Zustandsändernde Aktionen prüfen Authentifizierung, Berechtigung und CSRF-Schutz. Bei Objektzugriff per ID wird
  geprüft, ob der Nutzer genau dieses Objekt sehen bzw. ändern darf (IDOR).
- Datenbankzugriffe nutzen ausschließlich Prepared Statements. Spalten- und Sortiernamen kommen aus Whitelists.
- Uploads werden auf Typ und Größe geprüft und nicht ausführbar abgelegt.
- Server-seitige Requests auf URLs von außen sind gegen interne Ziele abgesichert (SSRF).
  Weiterleitungen gehen nur auf erlaubte Ziele.
- eval, Deserialisierung fremder Daten, dynamische includes und Shell-Aufrufe werden nicht verwendet.
- Secrets stehen nie im Code, sondern in Umgebungsvariablen bzw. Server-Konfiguration.
- Debug-Ausgaben und Fehlerdetails sind in Produktion abgeschaltet.

## Lizenzen

- Fremdcode, Bibliotheken, Schriften und Icon-Sets werden nur mit kompatibler Lizenz übernommen und in
  THIRD-PARTY-LICENSES.md mit Name, Version, Lizenz und Quelle eingetragen.
- Code aus kommerziellen Produkten sowie Bilder und Logos unklarer Herkunft werden nicht übernommen.

## Rechtstexte

- Impressum, Datenschutzerklärung und Cookie-Texte formuliert Claude nicht selbst. Es werden nur Seiten bzw.
  Platzhalter angelegt, mit dem Hinweis, dass der Inhalt aus einem Generator oder von einer Fachperson stammen muss.
- Impressum und Datenschutzerklärung sind von jeder Seite mit einem Klick erreichbar, auch aus dem Cookie-Banner.

## Vor "fertig"

1. Keine neuen externen Domains, oder sie sind unter "Neue Drittanbieter" aufgeführt und consent-gesteuert.
2. Neue Eingaben validiert, Ausgaben escaped, Berechtigungen geprüft.
3. Neue Bibliotheken und Schriften in THIRD-PARTY-LICENSES.md eingetragen.
