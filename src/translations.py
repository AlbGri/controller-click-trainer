"""Sistema di traduzioni per l'interfaccia grafica.

Supporta inglese (default) e italiano.
"""

# Traduzioni complete per l'applicazione
TRANSLATIONS = {
    "en": {
        # Window
        "window_title": "Controller Click Trainer - Press Duration",

        # Stats Panel
        "stats_frame": "Press Duration",
        "last": "Last:",
        "ms": "ms",
        "total_presses": "Total presses:",
        "min_duration": "Min duration:",
        "avg_duration": "Avg duration:",
        "max_duration": "Max duration:",
        "below_threshold": "Below threshold:",
        "session_time": "Session time:",

        # Config Panel
        "config_frame": "Configuration",
        "profile": "Profile:",
        "threshold_duration": "Threshold duration (ms):",
        "button": "Button:",
        "all_buttons": "All",
        "apply": "Apply",

        # Action Buttons
        "start": "Start",
        "stop": "Stop",
        "save_session": "Save session",
        "history_charts": "History charts",
        "export_data": "Export data",

        # Chart Panel
        "chart_frame": "Real-Time Press Duration (bar = 1 press)",

        # Diagnostics Panel
        "diagnostics_frame": "Connection Diagnostics",
        "controller": "Controller:",
        "connection": "Connection:",
        "polling_rate": "Polling rate:",
        "latency": "Latency:",
        "jitter": "Jitter:",
        "quality": "Quality:",
        "no_controller": "No controller",

        # Log Panel
        "log_frame": "Recent presses",

        # Messages
        "controller_not_found": "Controller not found",
        "controller_not_found_msg": (
            "No controller detected.\n\n"
            "Verify that the controller is connected and recognized by Windows.\n"
            "If using DS4Windows, ensure Xbox emulation is active."
        ),
        "no_data": "No data",
        "no_data_to_save": "The session contains no presses to save.",
        "saved": "Saved",
        "session_saved": "Session saved successfully.",
        "error": "Error",
        "save_error": "Error during save.",
        "no_history": "No saved sessions for this profile.",
        "export_success": "Data exported to:\n{path}",
        "export_error": "No data to export or write error.",

        # Profile Dialog
        "new_profile": "New profile",
        "profile_name": "Profile name:",
        "create": "Create",
        "profile_exists": "Profile '{name}' already exists.",

        # Export Dialog
        "export_title": "Export data",

        # History Window
        "history_window_title": "History Charts - Press Duration",
        "tab_progress": "Progress",
        "tab_distribution": "Distribution",
        "tab_diagnostics": "Diagnostics",
        "tab_detail": "Duration details",
        "tab_report": "Report",

        # Chart
        "threshold_label": "Threshold:",
        "chart_x_axis": "Press #",
        "chart_y_axis": "Duration (ms)",

        # Report
        "report_total_sessions": "Total sessions: {count}",
        "report_press_duration": "--- Press Duration ---",
        "report_best_min": "  Best minimum:    {value} ms",
        "report_avg_sessions": "  Sessions avg:    {value} ms",
        "report_trend": "  Trend:           {value}",
        "report_statistical": "--- Statistical Analysis ---",
        "report_median": "  Median:          {value} ms",
        "report_percentile_10": "  Percentile 10:   {value} ms",
        "report_percentile_90": "  Percentile 90:   {value} ms",
        "report_std_dev": "  Std deviation:   {value} ms",
        "report_latency": "--- Controller Latency ---",
        "report_avg": "  Average:  {value} ms",
        "report_best": "  Best:     {value} ms",
        "report_jitter": "--- Jitter ---",
        "report_avg_jitter": "  Average: {value} ms",
        "report_connection": "--- Connection Comparison ---",
        "report_conn_sessions": "    Sessions:         {value}",
        "report_conn_latency": "    Avg latency:      {value} ms",
        "report_conn_best": "    Best min press:   {value} ms",
    },

    "it": {
        # Window
        "window_title": "Controller Click Trainer - Durata Pressioni",

        # Stats Panel
        "stats_frame": "Durata Pressioni",
        "last": "Ultima:",
        "ms": "ms",
        "total_presses": "Pressioni totali:",
        "min_duration": "Durata minima:",
        "avg_duration": "Durata media:",
        "max_duration": "Durata massima:",
        "below_threshold": "Sotto soglia:",
        "session_time": "Tempo sessione:",

        # Config Panel
        "config_frame": "Configurazione",
        "profile": "Profilo:",
        "threshold_duration": "Soglia durata (ms):",
        "button": "Pulsante:",
        "all_buttons": "Tutti",
        "apply": "Applica",

        # Action Buttons
        "start": "Avvia",
        "stop": "Ferma",
        "save_session": "Salva sessione",
        "history_charts": "Grafici storici",
        "export_data": "Esporta dati",

        # Chart Panel
        "chart_frame": "Durata Pressioni Real-Time (barra = 1 pressione)",

        # Diagnostics Panel
        "diagnostics_frame": "Diagnostica Connessione",
        "controller": "Controller:",
        "connection": "Connessione:",
        "polling_rate": "Polling rate:",
        "latency": "Latenza:",
        "jitter": "Jitter:",
        "quality": "Qualita:",
        "no_controller": "Nessun controller",

        # Log Panel
        "log_frame": "Ultime pressioni",

        # Messages
        "controller_not_found": "Controller non trovato",
        "controller_not_found_msg": (
            "Nessun controller rilevato.\n\n"
            "Verifica che il controller sia collegato e riconosciuto da Windows.\n"
            "Se usi DS4Windows, assicurati che l'emulazione Xbox sia attiva."
        ),
        "no_data": "Nessun dato",
        "no_data_to_save": "La sessione non contiene pressioni da salvare.",
        "saved": "Salvato",
        "session_saved": "Sessione salvata correttamente.",
        "error": "Errore",
        "save_error": "Errore durante il salvataggio.",
        "no_history": "Non ci sono sessioni salvate per questo profilo.",
        "export_success": "Dati esportati in:\n{path}",
        "export_error": "Nessun dato da esportare o errore di scrittura.",

        # Profile Dialog
        "new_profile": "Nuovo profilo",
        "profile_name": "Nome profilo:",
        "create": "Crea",
        "profile_exists": "Profilo '{name}' esiste gia.",

        # Export Dialog
        "export_title": "Esporta dati",

        # History Window
        "history_window_title": "Grafici Storici - Durata Pressioni",
        "tab_progress": "Progressi",
        "tab_distribution": "Distribuzione",
        "tab_diagnostics": "Diagnostica",
        "tab_detail": "Dettaglio durate",
        "tab_report": "Report",

        # Chart
        "threshold_label": "Soglia:",
        "chart_x_axis": "Pressione #",
        "chart_y_axis": "Durata (ms)",

        # Report
        "report_total_sessions": "Sessioni totali: {count}",
        "report_press_duration": "--- Durata Pressioni ---",
        "report_best_min": "  Best minimo:     {value} ms",
        "report_avg_sessions": "  Media sessioni:  {value} ms",
        "report_trend": "  Trend:           {value}",
        "report_statistical": "--- Analisi Statistica ---",
        "report_median": "  Mediana:         {value} ms",
        "report_percentile_10": "  Percentile 10:   {value} ms",
        "report_percentile_90": "  Percentile 90:   {value} ms",
        "report_std_dev": "  Deviazione std:  {value} ms",
        "report_latency": "--- Latenza Controller ---",
        "report_avg": "  Media:    {value} ms",
        "report_best": "  Migliore: {value} ms",
        "report_jitter": "--- Jitter ---",
        "report_avg_jitter": "  Medio: {value} ms",
        "report_connection": "--- Confronto Connessione ---",
        "report_conn_sessions": "    Sessioni:         {value}",
        "report_conn_latency": "    Latenza media:    {value} ms",
        "report_conn_best": "    Best min press:   {value} ms",
    }
}


def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Ottiene il testo tradotto per la chiave specificata.

    Args:
        key: Chiave di traduzione
        lang: Codice lingua ('en' o 'it')
        **kwargs: Parametri per formattazione del testo

    Returns:
        Testo tradotto
    """
    if lang not in TRANSLATIONS:
        lang = "en"

    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text

    return text


def get_flag_emoji(lang: str) -> str:
    """Restituisce il codice lingua per il selettore.

    Args:
        lang: Codice lingua ('en' o 'it')

    Returns:
        Codice lingua da visualizzare
    """
    flags = {
        "en": "EN",
        "it": "IT"
    }
    return flags.get(lang, "EN")


def get_next_language(current_lang: str) -> str:
    """Alterna tra le lingue disponibili.

    Args:
        current_lang: Lingua corrente

    Returns:
        Prossima lingua
    """
    return "it" if current_lang == "en" else "en"
