"""Modulo diagnostica avanzata per controller.

Analisi polling rate reale (dal thread input), latenza, jitter,
qualita connessione e analisi durata pressioni per identificare
anomalie del controller.
"""

import logging
from dataclasses import dataclass
logger = logging.getLogger(__name__)


@dataclass
class DiagnosticSnapshot:
    """Snapshot diagnostico in un dato istante."""
    polling_rate_hz: float
    latency_avg_ms: float
    latency_min_ms: float
    latency_max_ms: float
    jitter_ms: float
    connection_quality: str


class ControllerDiagnostics:
    """Diagnostica avanzata per monitoraggio qualita controller.

    Analizza i dati di polling rate e latenza dal ControllerMonitor
    e fornisce valutazioni sulla qualita della connessione.
    Analizza le durate delle pressioni per rilevare anomalie.
    """

    # Soglie qualita connessione basate su polling rate reale
    QUALITY_THRESHOLDS = {
        "Ottima": {"polling_min": 200, "jitter_max": 2.0},
        "Buona": {"polling_min": 100, "jitter_max": 5.0},
        "Discreta": {"polling_min": 50, "jitter_max": 10.0},
    }

    def evaluate_connection(self, polling_rate: float, latency_stats: dict) -> str:
        """Valuta la qualita della connessione.

        Args:
            polling_rate: Hz dal ControllerMonitor
            latency_stats: dict dal ControllerMonitor.get_latency_stats()

        Returns:
            stringa qualita: "Ottima", "Buona", "Discreta", "Scarsa" o "N/D"
        """
        if polling_rate == 0:
            return "N/D"

        jitter = latency_stats.get("jitter", 0)

        for quality, thresholds in self.QUALITY_THRESHOLDS.items():
            if (polling_rate >= thresholds["polling_min"] and
                    jitter <= thresholds["jitter_max"]):
                return quality

        return "Scarsa"

    def take_snapshot(self, polling_rate: float, latency_stats: dict) -> DiagnosticSnapshot:
        """Cattura uno snapshot diagnostico.

        Args:
            polling_rate: Hz corrente
            latency_stats: statistiche latenza correnti
        """
        return DiagnosticSnapshot(
            polling_rate_hz=round(polling_rate, 1),
            latency_avg_ms=latency_stats.get("avg", 0),
            latency_min_ms=latency_stats.get("min", 0),
            latency_max_ms=latency_stats.get("max", 0),
            jitter_ms=latency_stats.get("jitter", 0),
            connection_quality=self.evaluate_connection(polling_rate, latency_stats),
        )

    def analyze_press_durations(self, durations_ms: list[float]) -> dict:
        """Analizza le durate delle pressioni per rilevare anomalie.

        Rileva se il controller sta "allungando" gli input o se ci sono
        inconsistenze tra pressioni rapide.

        Args:
            durations_ms: lista di durate in millisecondi

        Returns:
            dict con analisi dettagliata
        """
        if not durations_ms:
            return {"error": "Nessun dato"}

        n = len(durations_ms)
        avg = sum(durations_ms) / n
        min_val = min(durations_ms)
        max_val = max(durations_ms)
        variance = sum((x - avg) ** 2 for x in durations_ms) / n
        std_dev = variance ** 0.5

        # Mediana
        sorted_d = sorted(durations_ms)
        if n % 2 == 0:
            median = (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2
        else:
            median = sorted_d[n // 2]

        # Percentili
        p10 = sorted_d[max(0, int(n * 0.1))]
        p90 = sorted_d[min(n - 1, int(n * 0.9))]

        # Risoluzione minima del controller: la durata minima indica
        # il limite hardware/software di quanto breve puo' essere un input
        min_resolution = min_val

        # Analisi clustering: quante pressioni sono sotto varie soglie
        under_50ms = sum(1 for d in durations_ms if d <= 50)
        under_100ms = sum(1 for d in durations_ms if d <= 100)

        # Consistenza: quanto sono uniformi i tap rapidi (sotto mediana)
        fast_presses = [d for d in durations_ms if d <= median]
        fast_std = 0.0
        if len(fast_presses) > 1:
            fast_avg = sum(fast_presses) / len(fast_presses)
            fast_var = sum((x - fast_avg) ** 2 for x in fast_presses) / len(fast_presses)
            fast_std = fast_var ** 0.5

        return {
            "campioni": n,
            "media_ms": round(avg, 2),
            "mediana_ms": round(median, 2),
            "min_ms": round(min_val, 2),
            "max_ms": round(max_val, 2),
            "std_dev_ms": round(std_dev, 2),
            "percentile_10": round(p10, 2),
            "percentile_90": round(p90, 2),
            "risoluzione_minima_ms": round(min_resolution, 2),
            "sotto_50ms": under_50ms,
            "sotto_50ms_pct": round(under_50ms / n * 100, 1),
            "sotto_100ms": under_100ms,
            "sotto_100ms_pct": round(under_100ms / n * 100, 1),
            "consistenza_tap_rapidi_std": round(fast_std, 2),
        }

    def compare_sessions(self, sessions: list[dict]) -> dict:
        """Genera un report comparativo tra sessioni.

        Args:
            sessions: lista di dict con dati sessione (dal DataManager)

        Returns:
            dict con analisi comparativa
        """
        if not sessions:
            return {"error": "Nessuna sessione da confrontare"}

        min_durations = [s.get("min_duration_ms", 0) for s in sessions]
        avg_durations = [s.get("avg_duration_ms", 0) for s in sessions]
        latencies = [s.get("latency_avg_ms", 0) for s in sessions]
        jitters = [s.get("jitter_ms", 0) for s in sessions]

        return {
            "sessioni_totali": len(sessions),
            "durata_pressione": {
                "best_min_ms": round(min(min_durations), 2) if min_durations else 0,
                "media_avg_ms": round(sum(avg_durations) / len(avg_durations), 2) if avg_durations else 0,
                "trend": self._calculate_trend(min_durations),
            },
            "latenza": {
                "media_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
                "migliore_ms": round(min(latencies), 2) if latencies else 0,
            },
            "jitter": {
                "medio_ms": round(sum(jitters) / len(jitters), 2) if jitters else 0,
            },
        }

    @staticmethod
    def _calculate_trend(values: list[float]) -> str:
        """Calcola il trend di una serie (per durate: piu' basso = migliore).

        Args:
            values: serie di valori temporali

        Returns:
            "miglioramento", "peggioramento" o "stabile"
        """
        if len(values) < 3:
            return "dati insufficienti"

        mid = len(values) // 2
        first_half = sum(values[:mid]) / mid
        second_half = sum(values[mid:]) / (len(values) - mid)

        if first_half == 0:
            return "stabile"

        diff_pct = ((second_half - first_half) / first_half * 100)

        # Per le durate: diminuire e' migliorare
        if diff_pct < -5:
            return "miglioramento"
        elif diff_pct > 5:
            return "peggioramento"
        return "stabile"

    def get_connection_comparison(self, sessions: list[dict]) -> dict:
        """Confronta prestazioni USB vs Bluetooth.

        Args:
            sessions: lista di dict con dati sessione
        """
        result = {}
        for label in ["USB", "Bluetooth"]:
            group = [s for s in sessions if s.get("connection_type") == label]
            if group:
                latencies = [s.get("latency_avg_ms", 0) for s in group]
                min_durs = [s.get("min_duration_ms", 0) for s in group]
                result[label] = {
                    "sessioni": len(group),
                    "latenza_media_ms": round(sum(latencies) / len(latencies), 2),
                    "best_min_press_ms": round(min(min_durs), 2) if min_durs else 0,
                }
            else:
                result[label] = {"sessioni": 0, "latenza_media_ms": 0, "best_min_press_ms": 0}

        return result
