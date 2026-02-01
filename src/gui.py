"""Interfaccia grafica principale con tkinter.

Layout: statistiche durata pressioni, grafico a barre real-time,
configurazione soglie/profilo, diagnostica connessione e
log ultime pressioni.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from .controller_monitor import ControllerMonitor, PressEvent
from .data_manager import DataManager
from .diagnostics import ControllerDiagnostics
from .visualizer import RealtimeChart, HistoryVisualizer
from .translations import get_text, get_flag_emoji, get_next_language

logger = logging.getLogger(__name__)


class App:
    """Finestra principale dell'applicazione."""

    WINDOW_MIN_SIZE = (960, 750)

    def __init__(self):
        """Inizializza l'applicazione e tutti i componenti."""
        self.root = tk.Tk()
        self.root.minsize(*self.WINDOW_MIN_SIZE)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Componenti business
        self.data_manager = DataManager()
        self.settings = self.data_manager.load_settings()

        # Lingua (carica da settings)
        self._current_lang = self.settings.get("lingua", "en")
        self.root.title(self._t("window_title"))

        self.monitor = ControllerMonitor(
            threshold_ms=self.settings.get("soglia_durata_ms_default", 50.0)
        )
        self.diagnostics = ControllerDiagnostics()
        self.history_viz = HistoryVisualizer(
            colors=self.settings.get("colori", {})
        )

        # Stato
        self._update_job: Optional[str] = None
        self._session_active = False
        # Coda thread-safe per pressioni dal thread monitor
        self._pending_presses: list[PressEvent] = []
        self._pending_lock = __import__("threading").Lock()

        # Colori dal settings
        self._colors = self.settings.get("colori", {
            "sopra_soglia": "#2ecc71",
            "sotto_soglia": "#e74c3c",
            "sfondo": "#2c3e50",
            "testo": "#ecf0f1",
            "grafico_linea": "#3498db",
            "grafico_soglia": "#e67e22",
        })

        self._setup_style()
        self._build_ui()

        # Seleziona profilo default
        self.data_manager.select_profile(
            self.settings.get("profilo_default", "default")
        )
        self._refresh_profile_list()

        # Callback: quando il monitor completa una pressione, accoda per la GUI
        self.monitor.set_callback(on_press_complete=self._on_press_from_thread)

    def _setup_style(self) -> None:
        """Configura tema e stili ttk."""
        style = ttk.Style()
        style.theme_use("clam")

        bg = self._colors["sfondo"]
        fg = self._colors["testo"]

        self.root.configure(bg=bg)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"),
                        background=bg, foreground=fg)
        style.configure("Big.TLabel", font=("Segoe UI", 28, "bold"),
                        background=bg, foreground=fg)
        style.configure("Stats.TLabel", font=("Segoe UI", 12),
                        background=bg, foreground=fg)
        style.configure("Status.TLabel", font=("Segoe UI", 9),
                        background=bg, foreground="#95a5a6")
        style.configure("Green.TLabel", foreground=self._colors["sopra_soglia"],
                        background=bg, font=("Segoe UI", 28, "bold"))
        style.configure("Red.TLabel", foreground=self._colors["sotto_soglia"],
                        background=bg, font=("Segoe UI", 28, "bold"))
        style.configure("SmallGreen.TLabel", foreground=self._colors["sopra_soglia"],
                        background=bg, font=("Segoe UI", 10))
        style.configure("SmallRed.TLabel", foreground=self._colors["sotto_soglia"],
                        background=bg, font=("Segoe UI", 10))
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg,
                        font=("Segoe UI", 10, "bold"))

    def _t(self, key: str, **kwargs) -> str:
        """Helper per ottenere testi tradotti.

        Args:
            key: Chiave di traduzione
            **kwargs: Parametri per formattazione

        Returns:
            Testo tradotto nella lingua corrente
        """
        return get_text(key, self._current_lang, **kwargs)

    def _save_language(self) -> None:
        """Salva la lingua corrente nei settings."""
        self.settings["lingua"] = self._current_lang
        self.data_manager.save_settings(self.settings)

    def _switch_language(self) -> None:
        """Cambia la lingua dell'interfaccia."""
        # Alterna lingua
        self._current_lang = get_next_language(self._current_lang)

        # Aggiorna titolo finestra
        self.root.title(self._t("window_title"))

        # Aggiorna bandiera
        self._btn_flag.config(text=get_flag_emoji(self._current_lang))

        # Aggiorna frames
        self._stats_frame.config(text=self._t("stats_frame"))
        self._config_frame.config(text=self._t("config_frame"))
        self._chart_frame.config(text=self._t("chart_frame"))
        self._diag_frame.config(text=self._t("diagnostics_frame"))
        self._log_frame.config(text=self._t("log_frame"))

        # Aggiorna label stats panel
        self._lbl_last_label.config(text=self._t("last"))
        self._lbl_ms.config(text=self._t("ms"))
        for lbl, key in self._stats_labels_text:
            lbl.config(text=self._t(key))

        # Aggiorna label config panel
        self._lbl_profile.config(text=self._t("profile"))
        self._lbl_threshold.config(text=self._t("threshold_duration"))
        self._lbl_button.config(text=self._t("button"))
        self._btn_apply.config(text=self._t("apply"))

        # Aggiorna pulsanti azione
        self._btn_start.config(text=self._t("start"))
        self._btn_stop.config(text=self._t("stop"))
        self._btn_save.config(text=self._t("save_session"))
        self._btn_history.config(text=self._t("history_charts"))
        self._btn_export.config(text=self._t("export_data"))

        # Aggiorna combo button
        current_button = self._combo_button.get()
        # Mappa "Tutti" <-> "All"
        if current_button in ["Tutti", "All"]:
            self._combo_button.set(self._t("all_buttons"))
            current_button = None
        self._combo_button["values"] = [self._t("all_buttons")] + self.monitor.get_available_buttons()

        # Aggiorna label diagnostica
        for lbl, key in self._diag_labels_text:
            lbl.config(text=self._t(key))

        # Aggiorna label soglia e assi nel grafico
        self._chart.set_threshold_label(self._t("threshold_label"))
        self._chart.set_axis_labels(self._t("chart_x_axis"), self._t("chart_y_axis"))

        # Salva preferenza
        self._save_language()

        logger.info(f"Lingua cambiata a: {self._current_lang}")

    def _build_ui(self) -> None:
        """Costruisce l'intera interfaccia grafica."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 5))

        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill="both", expand=True, pady=5)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(5, 0))

        self._build_stats_panel(top_frame)
        self._build_config_panel(top_frame)
        self._build_chart_panel(mid_frame)
        self._build_bottom_panel(bottom_frame)

    def _build_stats_panel(self, parent: ttk.Frame) -> None:
        """Pannello statistiche: durata ultima pressione e statistiche sessione."""
        self._stats_frame = ttk.LabelFrame(parent, text=self._t("stats_frame"), padding=10)
        self._stats_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Durata ultima pressione (grande)
        dur_frame = ttk.Frame(self._stats_frame)
        dur_frame.pack(fill="x", pady=(0, 10))

        self._lbl_last_label = ttk.Label(dur_frame, text=self._t("last"), style="Stats.TLabel")
        self._lbl_last_label.pack(side="left")
        self._lbl_duration = ttk.Label(dur_frame, text="- -", style="Big.TLabel")
        self._lbl_duration.pack(side="left", padx=(10, 0))
        self._lbl_ms = ttk.Label(dur_frame, text=self._t("ms"), style="Stats.TLabel")
        self._lbl_ms.pack(side="left", padx=(5, 0))

        # Griglia statistiche
        grid_frame = ttk.Frame(self._stats_frame)
        grid_frame.pack(fill="x")

        # Salvo le label per poterle aggiornare quando cambia la lingua
        self._stats_labels_text = []
        labels = [
            ("total_presses", "_lbl_total", "0"),
            ("min_duration", "_lbl_min", "- -"),
            ("avg_duration", "_lbl_avg", "- -"),
            ("max_duration", "_lbl_max", "- -"),
            ("below_threshold", "_lbl_successes", "0 / 0"),
            ("session_time", "_lbl_session_time", "00:00"),
        ]
        for i, (key, attr, default) in enumerate(labels):
            lbl_text = ttk.Label(grid_frame, text=self._t(key), style="Stats.TLabel")
            lbl_text.grid(row=i, column=0, sticky="w", pady=2)
            self._stats_labels_text.append((lbl_text, key))

            lbl = ttk.Label(grid_frame, text=default, style="Stats.TLabel")
            lbl.grid(row=i, column=1, sticky="w", padx=(10, 0), pady=2)
            setattr(self, attr, lbl)

    def _build_config_panel(self, parent: ttk.Frame) -> None:
        """Pannello configurazione: profilo, soglia, pulsante, azioni."""
        self._config_frame = ttk.LabelFrame(parent, text=self._t("config_frame"), padding=10)
        self._config_frame.pack(side="right", fill="both", padx=(5, 0))

        # Frame superiore: profilo + bandiera
        top_config_frame = ttk.Frame(self._config_frame)
        top_config_frame.pack(fill="x", pady=(0, 8))

        # Profilo (a sinistra)
        profile_container = ttk.Frame(top_config_frame)
        profile_container.pack(side="left", fill="x", expand=True)

        self._lbl_profile = ttk.Label(profile_container, text=self._t("profile"))
        self._lbl_profile.pack(anchor="w")
        profile_frame = ttk.Frame(profile_container)
        profile_frame.pack(fill="x", pady=(2, 0))

        self._combo_profile = ttk.Combobox(profile_frame, state="readonly", width=15)
        self._combo_profile.pack(side="left")
        self._combo_profile.bind("<<ComboboxSelected>>", self._on_profile_change)

        ttk.Button(profile_frame, text="+", width=3,
                   command=self._on_new_profile).pack(side="left", padx=(5, 0))

        # Selettore lingua (a destra)
        flag_container = ttk.Frame(top_config_frame)
        flag_container.pack(side="right", padx=(15, 0))

        # Label lingua cliccabile (EN/IT)
        self._btn_flag = ttk.Label(
            flag_container,
            text=get_flag_emoji(self._current_lang),
            font=("Segoe UI", 10, "underline"),
            cursor="hand2",
            foreground=self._colors["testo"]
        )
        self._btn_flag.pack(anchor="n", pady=(2, 0))
        self._btn_flag.bind("<Button-1>", lambda e: self._switch_language())

        # Soglia durata (in ms) - obiettivo: stare SOTTO
        self._lbl_threshold = ttk.Label(self._config_frame, text=self._t("threshold_duration"))
        self._lbl_threshold.pack(anchor="w")
        threshold_frame = ttk.Frame(self._config_frame)
        threshold_frame.pack(fill="x", pady=(2, 8))

        self._var_threshold = tk.DoubleVar(
            value=self.settings.get("soglia_durata_ms_default", 50.0)
        )
        self._spin_threshold = ttk.Spinbox(
            threshold_frame, from_=5.0, to=500.0, increment=5.0,
            textvariable=self._var_threshold, width=8
        )
        self._spin_threshold.pack(side="left")
        self._btn_apply = ttk.Button(threshold_frame, text=self._t("apply"),
                   command=self._on_threshold_change)
        self._btn_apply.pack(side="left", padx=(5, 0))

        # Pulsante da monitorare
        self._lbl_button = ttk.Label(self._config_frame, text=self._t("button"))
        self._lbl_button.pack(anchor="w")
        self._combo_button = ttk.Combobox(self._config_frame, state="readonly", width=15)
        self._combo_button["values"] = [self._t("all_buttons")] + self.monitor.get_available_buttons()
        self._combo_button.set(self._t("all_buttons"))
        self._combo_button.pack(fill="x", pady=(2, 8))
        self._combo_button.bind("<<ComboboxSelected>>", self._on_button_change)

        # Pulsanti azione
        btn_frame = ttk.Frame(self._config_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        self._btn_start = ttk.Button(btn_frame, text=self._t("start"),
                                      command=self._on_start)
        self._btn_start.pack(fill="x", pady=2)

        self._btn_stop = ttk.Button(btn_frame, text=self._t("stop"),
                                     command=self._on_stop, state="disabled")
        self._btn_stop.pack(fill="x", pady=2)

        self._btn_save = ttk.Button(btn_frame, text=self._t("save_session"),
                                     command=self._on_save, state="disabled")
        self._btn_save.pack(fill="x", pady=2)

        self._btn_history = ttk.Button(btn_frame, text=self._t("history_charts"),
                                        command=self._on_show_history)
        self._btn_history.pack(fill="x", pady=2)

        self._btn_export = ttk.Button(btn_frame, text=self._t("export_data"),
                                       command=self._on_export)
        self._btn_export.pack(fill="x", pady=2)

    def _build_chart_panel(self, parent: ttk.Frame) -> None:
        """Pannello con grafico a barre durata pressioni."""
        self._chart_frame = ttk.LabelFrame(
            parent, text=self._t("chart_frame"), padding=5
        )
        self._chart_frame.pack(fill="both", expand=True)

        self._chart = RealtimeChart(
            self._chart_frame,
            max_bars=40,
            threshold_ms=self.settings.get("soglia_durata_ms_default", 50.0),
            colors=self._colors,
            threshold_label=self._t("threshold_label"),
            x_axis_label=self._t("chart_x_axis"),
            y_axis_label=self._t("chart_y_axis"),
        )

    def _build_bottom_panel(self, parent: ttk.Frame) -> None:
        """Pannello inferiore: diagnostica + log pressioni."""
        bottom_container = ttk.Frame(parent)
        bottom_container.pack(fill="x")

        # Diagnostica connessione
        self._diag_frame = ttk.LabelFrame(bottom_container, text=self._t("diagnostics_frame"), padding=8)
        self._diag_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        grid = ttk.Frame(self._diag_frame)
        grid.pack(fill="x")

        # Salvo le label per poterle aggiornare quando cambia la lingua
        self._diag_labels_text = []
        diag_labels = [
            ("controller", "_lbl_controller", self._t("no_controller")),
            ("connection", "_lbl_connection", "-"),
            ("polling_rate", "_lbl_polling", "- Hz"),
            ("latency", "_lbl_latency", "- ms"),
            ("jitter", "_lbl_jitter", "- ms"),
            ("quality", "_lbl_quality", "-"),
        ]

        for i, (key, attr, default) in enumerate(diag_labels):
            col = (i % 3) * 2
            row = i // 3
            lbl_text = ttk.Label(grid, text=self._t(key), style="Status.TLabel")
            lbl_text.grid(row=row, column=col, sticky="w", padx=(0, 5), pady=2)
            self._diag_labels_text.append((lbl_text, key))

            lbl = ttk.Label(grid, text=default, style="Status.TLabel")
            lbl.grid(row=row, column=col + 1, sticky="w", padx=(0, 20), pady=2)
            setattr(self, attr, lbl)

        # Log ultime pressioni
        self._log_frame = ttk.LabelFrame(bottom_container, text=self._t("log_frame"), padding=8)
        self._log_frame.pack(side="right", fill="both", padx=(5, 0))

        self._log_text = tk.Text(
            self._log_frame, width=30, height=4, font=("Consolas", 9),
            bg=self._colors["sfondo"], fg=self._colors["testo"],
            insertbackground=self._colors["testo"], state="disabled",
            wrap="none"
        )
        self._log_text.pack(fill="both", expand=True)
        # Tag colori per il log
        self._log_text.tag_configure("good", foreground=self._colors["sopra_soglia"])
        self._log_text.tag_configure("bad", foreground=self._colors["sotto_soglia"])

    # --- Callback dal thread monitor ---

    def _on_press_from_thread(self, event: PressEvent) -> None:
        """Riceve pressione dal thread monitor. Accoda per elaborazione nel main thread."""
        with self._pending_lock:
            self._pending_presses.append(event)

    # --- Callback azioni utente ---

    def _on_start(self) -> None:
        """Avvia il monitoraggio."""
        self.monitor.set_threshold(self._var_threshold.get())

        selected = self._combo_button.get()
        # Gestisce sia "Tutti" che "All" (traduzione)
        if selected in ["Tutti", "All"]:
            self.monitor.set_monitored_button(None)
        else:
            self.monitor.set_monitored_button(selected)

        if not self.monitor.start():
            messagebox.showwarning(
                self._t("controller_not_found"),
                self._t("controller_not_found_msg")
            )
            return

        self._session_active = True
        self._chart.reset()

        # Reset log
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")

        # UI
        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._btn_save.config(state="disabled")
        self._lbl_controller.config(text=self.monitor.controller_name)
        self._lbl_connection.config(text=self.monitor.connection_type)

        self._schedule_update()
        logger.info("Monitoraggio avviato dall'interfaccia")

    def _on_stop(self) -> None:
        """Ferma il monitoraggio."""
        if self._update_job:
            self.root.after_cancel(self._update_job)
            self._update_job = None

        self.monitor.stop()
        self._session_active = False

        self._btn_start.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._btn_save.config(state="normal")

        logger.info("Monitoraggio fermato dall'interfaccia")

    def _on_save(self) -> None:
        """Salva la sessione corrente."""
        stats = self.monitor.stats
        duration = self.monitor.get_session_duration()
        latency = self.monitor.get_latency_stats()

        if stats.total_presses == 0:
            messagebox.showinfo(self._t("no_data"), self._t("no_data_to_save"))
            return

        avg_duration = self.monitor.get_avg_duration()
        min_dur = stats.min_duration_ms if stats.min_duration_ms != float("inf") else 0

        button_name = self._combo_button.get()

        success = self.data_manager.save_session(
            button=button_name,
            press_count=stats.total_presses,
            session_duration=duration,
            min_duration_ms=min_dur,
            avg_duration_ms=avg_duration,
            max_duration_ms=stats.max_duration_ms,
            connection_type=self.monitor.connection_type,
            latency_avg=latency["avg"],
            jitter=latency["jitter"],
            threshold_ms=self.monitor.threshold_ms,
            threshold_successes=stats.threshold_successes,
        )

        if success:
            messagebox.showinfo(self._t("saved"), self._t("session_saved"))
            self._btn_save.config(state="disabled")
        else:
            messagebox.showerror(self._t("error"), self._t("save_error"))

    def _on_show_history(self) -> None:
        """Mostra i grafici storici in finestre separate."""
        sessions = self.data_manager.load_sessions()
        if not sessions:
            messagebox.showinfo(
                self._t("no_data"),
                self._t("no_history")
            )
            return

        hist_window = tk.Toplevel(self.root)
        hist_window.title(self._t("history_window_title"))
        hist_window.configure(bg=self._colors["sfondo"])
        hist_window.geometry("850x700")

        notebook = ttk.Notebook(hist_window)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Tab Progressi
        fig_progress = self.history_viz.plot_progress(sessions)
        if fig_progress:
            tab1 = ttk.Frame(notebook)
            notebook.add(tab1, text=self._t("tab_progress"))
            canvas1 = FigureCanvasTkAgg(fig_progress, master=tab1)
            canvas1.get_tk_widget().pack(fill="both", expand=True)
            canvas1.draw()

        # Tab Distribuzione
        fig_dist = self.history_viz.plot_distribution(sessions)
        if fig_dist:
            tab2 = ttk.Frame(notebook)
            notebook.add(tab2, text=self._t("tab_distribution"))
            canvas2 = FigureCanvasTkAgg(fig_dist, master=tab2)
            canvas2.get_tk_widget().pack(fill="both", expand=True)
            canvas2.draw()

        # Tab Diagnostica
        fig_diag = self.history_viz.plot_diagnostics(sessions)
        if fig_diag:
            tab3 = ttk.Frame(notebook)
            notebook.add(tab3, text=self._t("tab_diagnostics"))
            canvas3 = FigureCanvasTkAgg(fig_diag, master=tab3)
            canvas3.get_tk_widget().pack(fill="both", expand=True)
            canvas3.draw()

        # Tab Analisi pressioni (dalla sessione corrente se disponibile)
        durations = [s.get("avg_duration_ms", 0) for s in sessions]
        if durations:
            fig_detail = self.history_viz.plot_session_detail(
                durations, self.monitor.threshold_ms
            )
            if fig_detail:
                tab4 = ttk.Frame(notebook)
                notebook.add(tab4, text=self._t("tab_detail"))
                canvas4 = FigureCanvasTkAgg(fig_detail, master=tab4)
                canvas4.get_tk_widget().pack(fill="both", expand=True)
                canvas4.draw()

        # Tab Report
        tab_report = ttk.Frame(notebook, padding=15)
        notebook.add(tab_report, text=self._t("tab_report"))
        self._build_report_tab(tab_report, sessions)

    def _build_report_tab(self, parent: ttk.Frame, sessions: list[dict]) -> None:
        """Costruisce il tab report comparativo."""
        report = self.diagnostics.compare_sessions(sessions)
        conn_report = self.diagnostics.get_connection_comparison(sessions)

        # Analisi pressioni se ci sono durate
        durations = [s.get("avg_duration_ms", 0) for s in sessions]
        press_analysis = self.diagnostics.analyze_press_durations(durations)

        text = tk.Text(parent, wrap="word", font=("Consolas", 10),
                       bg=self._colors["sfondo"], fg=self._colors["testo"],
                       insertbackground=self._colors["testo"])
        text.pack(fill="both", expand=True)

        dur = report.get("durata_pressione", {})
        lat = report.get("latenza", {})
        jit = report.get("jitter", {})

        lines = [
            self._t("report_total_sessions", count=report.get('sessioni_totali', 0)),
            "",
            self._t("report_press_duration"),
            self._t("report_best_min", value=dur.get('best_min_ms', 0)),
            self._t("report_avg_sessions", value=dur.get('media_avg_ms', 0)),
            self._t("report_trend", value=dur.get('trend', '-')),
            "",
            self._t("report_statistical"),
            self._t("report_median", value=press_analysis.get('mediana_ms', 0)),
            self._t("report_percentile_10", value=press_analysis.get('percentile_10', 0)),
            self._t("report_percentile_90", value=press_analysis.get('percentile_90', 0)),
            self._t("report_std_dev", value=press_analysis.get('std_dev_ms', 0)),
            "",
            self._t("report_latency"),
            self._t("report_avg", value=lat.get('media_ms', 0)),
            self._t("report_best", value=lat.get('migliore_ms', 0)),
            "",
            self._t("report_jitter"),
            self._t("report_avg_jitter", value=jit.get('medio_ms', 0)),
            "",
            self._t("report_connection"),
        ]

        for conn_type in ["USB", "Bluetooth"]:
            data = conn_report.get(conn_type, {})
            lines.append(f"  {conn_type}:")
            lines.append(self._t("report_conn_sessions", value=data.get('sessioni', 0)))
            lines.append(self._t("report_conn_latency", value=data.get('latenza_media_ms', 0)))
            lines.append(self._t("report_conn_best", value=data.get('best_min_press_ms', 0)))

        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")

    def _on_export(self) -> None:
        """Esporta tutti i dati in un file CSV."""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title=self._t("export_title")
        )
        if not path:
            return

        if self.data_manager.export_all_data(path):
            messagebox.showinfo(self._t("export_data"), self._t("export_success", path=path))
        else:
            messagebox.showerror(self._t("error"), self._t("export_error"))

    def _on_profile_change(self, _event=None) -> None:
        name = self._combo_profile.get()
        self.data_manager.select_profile(name)

    def _on_new_profile(self) -> None:
        """Crea un nuovo profilo utente."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self._t("new_profile"))
        dialog.geometry("300x120")
        dialog.configure(bg=self._colors["sfondo"])
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=self._t("profile_name")).pack(pady=(15, 5))
        entry = ttk.Entry(dialog, width=25)
        entry.pack(pady=5)
        entry.focus()

        def create():
            name = entry.get().strip()
            if name:
                if self.data_manager.create_profile(name):
                    self._refresh_profile_list()
                    self._combo_profile.set(name)
                    self.data_manager.select_profile(name)
                else:
                    messagebox.showwarning(self._t("error"), self._t("profile_exists", name=name))
            dialog.destroy()

        ttk.Button(dialog, text=self._t("create"), command=create).pack(pady=10)
        entry.bind("<Return>", lambda _: create())

    def _on_threshold_change(self) -> None:
        """Aggiorna la soglia durata."""
        try:
            value = self._var_threshold.get()
            self.monitor.set_threshold(value)
            self._chart.set_threshold(value)
        except (tk.TclError, ValueError):
            pass

    def _on_button_change(self, _event=None) -> None:
        selected = self._combo_button.get()
        # Gestisce sia "Tutti" che "All" (traduzione)
        if selected in ["Tutti", "All"]:
            self.monitor.set_monitored_button(None)
        else:
            self.monitor.set_monitored_button(selected)

    def _refresh_profile_list(self) -> None:
        profiles = self.data_manager.get_profiles()
        self._combo_profile["values"] = profiles
        if profiles:
            current = self.data_manager.current_profile or profiles[0]
            if current in profiles:
                self._combo_profile.set(current)
            else:
                self._combo_profile.set(profiles[0])

    # --- Loop aggiornamento UI ---

    def _schedule_update(self) -> None:
        if not self._session_active:
            return
        interval = self.settings.get("intervallo_aggiornamento_ms", 50)
        self._update_job = self.root.after(interval, self._update_ui)

    def _update_ui(self) -> None:
        """Aggiorna tutti gli elementi UI con i dati correnti."""
        if not self._session_active:
            return

        stats = self.monitor.stats

        # Processa pressioni accodate dal thread monitor
        with self._pending_lock:
            new_presses = list(self._pending_presses)
            self._pending_presses.clear()

        for press in new_presses:
            # Aggiorna grafico
            self._chart.add_press(press.duration_ms, press.button)
            # Aggiorna log
            self._append_log(press)

        # Durata ultima pressione (grande, colorata)
        if stats.last_duration_ms > 0:
            d = stats.last_duration_ms
            self._lbl_duration.config(text=f"{d:.1f}")
            if d <= self.monitor.threshold_ms:
                self._lbl_duration.config(style="Green.TLabel")
            else:
                self._lbl_duration.config(style="Red.TLabel")

        # Statistiche
        self._lbl_total.config(text=str(stats.total_presses))

        if stats.total_presses > 0:
            min_d = stats.min_duration_ms if stats.min_duration_ms != float("inf") else 0
            self._lbl_min.config(text=f"{min_d:.1f} ms")
            self._lbl_avg.config(text=f"{self.monitor.get_avg_duration():.1f} ms")
            self._lbl_max.config(text=f"{stats.max_duration_ms:.1f} ms")
            self._lbl_successes.config(
                text=f"{stats.threshold_successes} / {stats.total_presses}"
            )

        # Timer sessione
        duration = self.monitor.get_session_duration()
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        self._lbl_session_time.config(text=f"{minutes:02d}:{seconds:02d}")

        # Diagnostica (dal vero polling rate del thread input)
        polling = self.monitor.get_polling_rate()
        latency_stats = self.monitor.get_latency_stats()
        quality = self.diagnostics.evaluate_connection(polling, latency_stats)

        self._lbl_polling.config(text=f"{polling:.0f} Hz")
        self._lbl_latency.config(text=f"{latency_stats['avg']:.1f} ms")
        self._lbl_jitter.config(text=f"{latency_stats['jitter']:.1f} ms")
        self._lbl_quality.config(text=quality)

        self._schedule_update()

    def _append_log(self, press: PressEvent) -> None:
        """Aggiunge una riga al log pressioni."""
        self._log_text.config(state="normal")

        d = press.duration_ms
        tag = "good" if d <= self.monitor.threshold_ms else "bad"
        line = f"{press.button:>5s}  {d:7.1f} ms\n"

        self._log_text.insert("end", line, tag)

        # Limita righe visibili
        line_count = int(self._log_text.index("end-1c").split(".")[0])
        if line_count > 100:
            self._log_text.delete("1.0", "2.0")

        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _on_close(self) -> None:
        """Gestisce la chiusura dell'applicazione."""
        if self._session_active:
            self.monitor.stop()
        if self._update_job:
            self.root.after_cancel(self._update_job)
        self.root.destroy()

    def run(self) -> None:
        """Avvia il mainloop tkinter."""
        logger.info("Avvio interfaccia grafica")
        self.root.mainloop()
