# Sicherheits- und Datenschutz-Guidance für dieses WordPress-Projekt

Kontext: Öffentliche WordPress-Website eines Betreibers in Deutschland. Besucher sind
Endnutzer in der EU. Es gelten DSGVO und TDDDG. Angreifer sind anonyme Besucher, eingeloggte
Nutzer mit niedriger Rolle (Subscriber/Contributor) und automatisierte Bots.

## Als Befund melden (Sicherheit)

- Zustandsändernde Aktionen (AJAX `wp_ajax_*`, `admin_post_*`, Formular-Handler, REST-Callbacks)
  ohne Nonce-Prüfung (`check_ajax_referer`, `check_admin_referer`, `wp_verify_nonce`) **oder** ohne
  `current_user_can()` mit passender Capability. Eine Nonce allein ist keine Autorisierung.
- `is_admin()` als Berechtigungsprüfung.
- REST-Routen ohne `permission_callback` oder mit `__return_true`, sofern sie Daten ändern oder
  nicht-öffentliche Daten liefern (z. B. E-Mail-Adressen, Formular-Einsendungen, Nutzerlisten).
- SQL mit eingesetzten Variablen ohne `$wpdb->prepare()`. ORDER BY/Spaltennamen ohne Whitelist.
- Ausgabe ohne kontextgerechtes Escaping (`esc_html`, `esc_attr`, `esc_url`, `esc_js`, `wp_kses*`),
  auch bei Werten aus Optionen, Post-Meta oder User-Meta (Stored XSS über Low-Priv-Rollen).
- Eingaben aus Superglobals ohne `wp_unslash()` + Sanitizing.
- Uploads ohne `wp_check_filetype_and_ext()`, ohne Größenlimit oder mit Speicherung außerhalb des
  Upload-Verzeichnisses. Ausführbare Endungen (php, phtml, phar, svg ohne Sanitizing).
- `unserialize`/`maybe_unserialize` auf fremden Daten, `extract`, `eval`, dynamisches `include`.
- Server-seitige HTTP-Requests auf nutzerkontrollierte URLs ohne `wp_safe_remote_*` (SSRF).
- `wp_redirect()` auf nutzerkontrollierte Ziele (Open Redirect).
- IDOR: Zugriff auf Posts, Einsendungen, Bestellungen oder User-Daten per ID, ohne zu prüfen,
  ob der aktuelle Nutzer genau dieses Objekt sehen oder ändern darf.
- Secrets (API-Keys, SMTP-Zugangsdaten) im Code statt in `wp-config.php`/Umgebungsvariablen.
- Fehlendes `defined( 'ABSPATH' ) || exit;` in direkt aufrufbaren PHP-Dateien.

## Als Befund melden (Datenschutz)

- Jede Ressource, die beim Seitenaufruf von einem Drittserver geladen wird, ohne vorherige
  Einwilligung: Google Fonts, CDNs, YouTube/Vimeo/Maps/Social-Embeds, reCAPTCHA, Analytics/Pixel,
  Gravatar. Ausnahme: Die Zeile trägt den Kommentar `dsgvo-ok:` mit nachvollziehbarer Begründung
  (z. B. Laden erst nach Consent-Event).
- Nicht notwendige Cookies oder `localStorage`-Einträge, die ohne Einwilligung gesetzt werden.
- Speicherung personenbezogener Daten (Formulare, E-Mail, Telefon, IP) ohne erkennbaren Zweck,
  ohne Löschfrist oder in Logs.
- Weitergabe personenbezogener Daten an externe APIs ohne Hinweis im Code bzw. in der Antwort.

## Nicht melden

- Escaping-Funde in Code unter `vendor/`, `node_modules/`, `wp-admin/`, `wp-includes/`.
- `__return_true` als `permission_callback` bei Routen, die nachweislich nur öffentliche,
  ohnehin im Frontend sichtbare Daten lesen, wenn ein Kommentar das begründet.
