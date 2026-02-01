"""Modulo per la visualizzazione grafici con matplotlib.

Grafico real-time a barre della durata pressioni, grafici storici
di progressi, distribuzione durate e diagnostica.
"""

import logging
from typing import Optional

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
logger = logging.getLogger(__name__)


class RealtimeChart:
    """Grafico real-time delle durate pressioni, embedded in tkinter.

    Mostra barre verticali per ogni pressione: altezza = durata in ms.
    Colore verde se sotto soglia, rosso se sopra.
    """

    def __init__(
        self,
        parent_frame,
        max_bars: int = 40,
        threshold_ms: float = 50.0,
        colors: Optional[dict] = None,
        threshold_label: str = "Threshold:",
        x_axis_label: str = "Press #",
        y_axis_label: str = "Duration (ms)",
    ):
        """Inizializza il grafico real-time.

        Args:
            parent_frame: widget tkinter che conterra il grafico
            max_bars: numero massimo di barre visibili
            threshold_ms: soglia da visualizzare come linea orizzontale
            colors: dict con colori personalizzati
            threshold_label: label tradotta per la soglia
            x_axis_label: label tradotta per l'asse X
            y_axis_label: label tradotta per l'asse Y
        """
        self.max_bars = max_bars
        self.threshold_ms = threshold_ms
        self.threshold_label = threshold_label
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label

        colors = colors or {}
        self._color_threshold = colors.get("grafico_soglia", "#e67e22")
        self._color_bg = colors.get("sfondo", "#2c3e50")
        self._color_text = colors.get("testo", "#ecf0f1")
        self._color_above = colors.get("sopra_soglia", "#2ecc71")
        self._color_below = colors.get("sotto_soglia", "#e74c3c")

        # Dati: lista di (durata_ms, button_name)
        self._data: list[tuple[float, str]] = []

        # Crea figura matplotlib
        self._fig = Figure(figsize=(6, 2.8), dpi=100, facecolor=self._color_bg)
        self._ax = self._fig.add_subplot(111)
        self._setup_axes()

        # Linea soglia
        self._threshold_line = self._ax.axhline(
            y=self.threshold_ms, color=self._color_threshold,
            linestyle="--", linewidth=1.5, alpha=0.9,
            label=f"{self.threshold_label} {self.threshold_ms:.0f} ms"
        )
        self._ax.legend(loc="upper right", fontsize=8,
                        facecolor=self._color_bg, edgecolor=self._color_text,
                        labelcolor=self._color_text)

        # Embed in tkinter
        self._canvas = FigureCanvasTkAgg(self._fig, master=parent_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._fig.tight_layout(pad=1.0)

    def _setup_axes(self) -> None:
        """Configura stile degli assi."""
        self._ax.set_facecolor(self._color_bg)
        self._ax.set_xlabel(self.x_axis_label, color=self._color_text, fontsize=9)
        self._ax.set_ylabel(self.y_axis_label, color=self._color_text, fontsize=9)
        self._ax.tick_params(colors=self._color_text, labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_color(self._color_text)
            spine.set_alpha(0.3)
        self._ax.grid(True, axis="y", alpha=0.15, color=self._color_text)

    def reset(self) -> None:
        """Resetta il grafico per una nuova sessione."""
        self._data.clear()
        self._ax.clear()
        self._setup_axes()
        self._threshold_line = self._ax.axhline(
            y=self.threshold_ms, color=self._color_threshold,
            linestyle="--", linewidth=1.5, alpha=0.9,
            label=f"{self.threshold_label} {self.threshold_ms:.0f} ms"
        )
        self._ax.legend(loc="upper right", fontsize=8,
                        facecolor=self._color_bg, edgecolor=self._color_text,
                        labelcolor=self._color_text)
        self._canvas.draw_idle()

    def add_press(self, duration_ms: float, button: str) -> None:
        """Aggiunge una pressione e ridisegna.

        Args:
            duration_ms: durata della pressione in ms
            button: nome del pulsante
        """
        self._data.append((duration_ms, button))

        # Limita il numero di barre visibili
        if len(self._data) > self.max_bars:
            self._data = self._data[-self.max_bars:]

        self._redraw()

    def _redraw(self) -> None:
        """Ridisegna tutte le barre."""
        self._ax.clear()
        self._setup_axes()

        if not self._data:
            self._canvas.draw_idle()
            return

        durations = [d[0] for d in self._data]
        n = len(durations)
        x = list(range(n))

        # Colori: verde se sotto soglia, rosso se sopra
        colors = [
            self._color_above if d <= self.threshold_ms else self._color_below
            for d in durations
        ]

        self._ax.bar(x, durations, color=colors, alpha=0.85, width=0.8)

        # Linea soglia
        self._ax.axhline(
            y=self.threshold_ms, color=self._color_threshold,
            linestyle="--", linewidth=1.5, alpha=0.9,
            label=f"{self.threshold_label} {self.threshold_ms:.0f} ms"
        )

        # Etichette durata sulle barre (solo se poche)
        if n <= 25:
            for i, d in enumerate(durations):
                self._ax.text(
                    i, d + max(durations) * 0.02, f"{d:.0f}",
                    ha="center", va="bottom",
                    fontsize=7, color=self._color_text, alpha=0.8
                )

        # Limiti Y dinamici
        y_max = max(max(durations) * 1.3, self.threshold_ms * 2)
        self._ax.set_ylim(0, y_max)

        self._ax.set_xticks(x[::max(1, n // 10)])

        self._ax.legend(loc="upper right", fontsize=8,
                        facecolor=self._color_bg, edgecolor=self._color_text,
                        labelcolor=self._color_text)

        try:
            self._fig.tight_layout(pad=1.0)
            self._canvas.draw_idle()
        except Exception:
            pass

    def set_threshold(self, value_ms: float) -> None:
        """Aggiorna la soglia visualizzata."""
        self.threshold_ms = value_ms
        self._redraw()

    def set_threshold_label(self, threshold_label: str) -> None:
        """Aggiorna la label della soglia (per cambio lingua).

        Args:
            threshold_label: nuova label tradotta
        """
        self.threshold_label = threshold_label
        self._redraw()

    def set_axis_labels(self, x_axis_label: str, y_axis_label: str) -> None:
        """Aggiorna le label degli assi (per cambio lingua).

        Args:
            x_axis_label: nuova label tradotta per asse X
            y_axis_label: nuova label tradotta per asse Y
        """
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label
        self._redraw()

    def get_figure(self) -> Figure:
        """Restituisce la figura matplotlib."""
        return self._fig


class HistoryVisualizer:
    """Genera grafici statici per lo storico sessioni (basati su durata)."""

    def __init__(self, colors: Optional[dict] = None):
        colors = colors or {}
        self._color_bg = colors.get("sfondo", "#2c3e50")
        self._color_text = colors.get("testo", "#ecf0f1")
        self._color_line = colors.get("grafico_linea", "#3498db")
        self._color_threshold = colors.get("grafico_soglia", "#e67e22")
        self._color_good = colors.get("sopra_soglia", "#2ecc71")
        self._color_bad = colors.get("sotto_soglia", "#e74c3c")

    def _style_ax(self, ax) -> None:
        """Applica lo stile standard a un asse."""
        ax.set_facecolor(self._color_bg)
        ax.tick_params(colors=self._color_text, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(self._color_text)
            spine.set_alpha(0.3)
        ax.grid(True, alpha=0.15, color=self._color_text)

    def plot_progress(self, sessions: list[dict]) -> Optional[Figure]:
        """Grafico progressi: durata min e media per sessione.

        Args:
            sessions: lista di dict sessioni dal DataManager
        """
        if len(sessions) < 2:
            return None

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(8, 6), facecolor=self._color_bg
        )

        indices = list(range(1, len(sessions) + 1))
        min_durs = [s.get("min_duration_ms", 0) for s in sessions]
        avg_durs = [s.get("avg_duration_ms", 0) for s in sessions]

        # Grafico durate
        self._style_ax(ax1)
        ax1.plot(indices, min_durs, "o-", color=self._color_good,
                 linewidth=2, markersize=5, label="Min (best)")
        ax1.plot(indices, avg_durs, "s-", color=self._color_line,
                 linewidth=1.5, markersize=4, label="Media")
        ax1.set_ylabel("Durata (ms)", color=self._color_text, fontsize=10)
        ax1.set_title("Progressi durata pressioni",
                      color=self._color_text, fontsize=12)
        ax1.legend(facecolor=self._color_bg, edgecolor=self._color_text,
                   labelcolor=self._color_text)
        # Per le durate, piu' basso e' meglio: inverti concettualmente
        ax1.invert_yaxis()

        # Grafico successi soglia
        successes = [s.get("threshold_successes", 0) for s in sessions]
        totals = [s.get("press_count", 1) for s in sessions]
        pcts = [round(s / t * 100, 1) if t > 0 else 0 for s, t in zip(successes, totals)]

        self._style_ax(ax2)
        ax2.bar(indices, pcts, color=self._color_good, alpha=0.7)
        ax2.set_xlabel("Sessione #", color=self._color_text, fontsize=10)
        ax2.set_ylabel("% sotto soglia", color=self._color_text, fontsize=10)
        ax2.set_ylim(0, 105)

        fig.tight_layout(pad=1.5)
        return fig

    def plot_distribution(self, sessions: list[dict]) -> Optional[Figure]:
        """Grafico distribuzione durate medie per sessione."""
        if not sessions:
            return None

        avg_durs = [s.get("avg_duration_ms", 0) for s in sessions]

        fig, ax = plt.subplots(figsize=(7, 4), facecolor=self._color_bg)
        self._style_ax(ax)

        n_bins = min(20, max(5, len(avg_durs) // 2))
        ax.hist(avg_durs, bins=n_bins, color=self._color_line,
                alpha=0.7, edgecolor=self._color_text, linewidth=0.5)
        ax.set_xlabel("Durata media pressione (ms)", color=self._color_text, fontsize=10)
        ax.set_ylabel("Frequenza", color=self._color_text, fontsize=10)
        ax.set_title("Distribuzione durate sessioni",
                     color=self._color_text, fontsize=12)

        fig.tight_layout(pad=1.5)
        return fig

    def plot_diagnostics(self, sessions: list[dict]) -> Optional[Figure]:
        """Grafico diagnostica: latenza e jitter nel tempo."""
        if len(sessions) < 2:
            return None

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(8, 6), facecolor=self._color_bg
        )

        indices = list(range(1, len(sessions) + 1))
        latencies = [s.get("latency_avg_ms", 0) for s in sessions]
        jitters = [s.get("jitter_ms", 0) for s in sessions]

        self._style_ax(ax1)
        ax1.plot(indices, latencies, "o-", color=self._color_threshold,
                 linewidth=2, markersize=5)
        ax1.set_ylabel("Latenza media (ms)", color=self._color_text, fontsize=10)
        ax1.set_title("Latenza e Jitter nel tempo",
                      color=self._color_text, fontsize=12)

        self._style_ax(ax2)
        ax2.plot(indices, jitters, "s-", color=self._color_bad,
                 linewidth=2, markersize=5)
        ax2.set_xlabel("Sessione #", color=self._color_text, fontsize=10)
        ax2.set_ylabel("Jitter (ms)", color=self._color_text, fontsize=10)

        fig.tight_layout(pad=1.5)
        return fig

    def plot_session_detail(self, durations_ms: list[float], threshold_ms: float) -> Optional[Figure]:
        """Grafico dettaglio singola sessione: ogni pressione come barra.

        Args:
            durations_ms: lista durate della sessione
            threshold_ms: soglia corrente
        """
        if not durations_ms:
            return None

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(8, 6), facecolor=self._color_bg
        )

        # Barre per ogni pressione
        self._style_ax(ax1)
        x = list(range(1, len(durations_ms) + 1))
        colors = [
            self._color_good if d <= threshold_ms else self._color_bad
            for d in durations_ms
        ]
        ax1.bar(x, durations_ms, color=colors, alpha=0.8, width=0.9)
        ax1.axhline(y=threshold_ms, color=self._color_threshold,
                     linestyle="--", linewidth=1.5, alpha=0.9)
        ax1.set_ylabel("Durata (ms)", color=self._color_text, fontsize=10)
        ax1.set_title("Durata ogni pressione", color=self._color_text, fontsize=12)

        # Istogramma distribuzione
        self._style_ax(ax2)
        n_bins = min(30, max(5, len(durations_ms) // 3))
        ax2.hist(durations_ms, bins=n_bins, color=self._color_line,
                 alpha=0.7, edgecolor=self._color_text, linewidth=0.5)
        ax2.axvline(x=threshold_ms, color=self._color_threshold,
                     linestyle="--", linewidth=1.5, alpha=0.9)
        ax2.set_xlabel("Durata (ms)", color=self._color_text, fontsize=10)
        ax2.set_ylabel("Frequenza", color=self._color_text, fontsize=10)

        fig.tight_layout(pad=1.5)
        return fig
