# WordPress-spezifische Konventionen

- Skripte und Styles werden per `wp_enqueue_script` / `wp_enqueue_style` mit lokalem Pfad eingebunden
  (`get_theme_file_uri()`, `plugins_url()`), nie per hart kodiertem `<script>`/`<link>` oder externer URL.
- Schriften im Block-Theme über `theme.json` → `fontFace` mit `file:./assets/fonts/...`.
- Gravatar wird deaktiviert oder lokal ersetzt. `print_emoji_detection_script` wird entfernt, wenn keine WP-Emojis nötig sind.
- Eingaben: `wp_unslash()` + `sanitize_text_field()` / `sanitize_email()` / `absint()` / Whitelist.
  Superglobals werden nie direkt weiterverwendet.
- Ausgaben werden spät escaped: `esc_html()`, `esc_attr()`, `esc_url()`, `esc_js()`, `wp_kses_post()`,
  auch bei Werten aus Optionen und Meta-Feldern.
- Jede zustandsändernde Aktion (Formular, `wp_ajax_*`, `admin_post_*`, REST) prüft eine Nonce
  (`check_ajax_referer`, `check_admin_referer`, `wp_verify_nonce`) **und** `current_user_can()`.
  `is_admin()` ist keine Berechtigungsprüfung.
- SQL nur über `$wpdb->prepare()` oder `$wpdb->insert/update/delete`.
- `register_rest_route` immer mit echtem `permission_callback`. `__return_true` nur für bewusst öffentliche,
  rein lesende Routen, mit Kommentar.
- `wp_ajax_nopriv_*` nur, wenn Gäste die Aktion wirklich brauchen.
- Uploads über `wp_handle_upload()` / `media_handle_upload()` mit `wp_check_filetype_and_ext()`. Kein `move_uploaded_file()`.
- Externe URLs von außen: `wp_safe_remote_get()` / `wp_safe_remote_post()`. Weiterleitungen: `wp_safe_redirect()` + `exit;`.
- Secrets als Konstanten in `wp-config.php` oder als Umgebungsvariablen.
- Jede PHP-Datei beginnt mit `defined( 'ABSPATH' ) || exit;`. Funktionen, Hooks, Optionen und Handles tragen das Projektpräfix.
- `WP_DEBUG_DISPLAY` ist in Produktion aus. Kein `var_dump`/`print_r` im ausgelieferten Code.
- Themes und Plugins stehen unter GPL-2.0-or-later. Gebündelter Fremdcode muss GPL-kompatibel sein
  (MIT, BSD, Apache-2.0, LGPL, GPL).
- Falls vorhanden, läuft `vendor/bin/phpcs` (WordPress-Standard) ohne neue Fehler.
