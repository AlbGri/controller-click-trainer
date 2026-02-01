"""Modulo per la gestione dati e profili utente.

Salvataggio statistiche sessioni in CSV (con focus su durata pressioni),
gestione profili multipli, export dati.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Intestazioni CSV per il file sessioni
CSV_HEADERS = [
    "timestamp",
    "username",
    "button",
    "press_count",
    "session_duration_s",
    "min_duration_ms",
    "avg_duration_ms",
    "max_duration_ms",
    "connection_type",
    "latency_avg_ms",
    "jitter_ms",
    "threshold_ms",
    "threshold_successes",
]


class DataManager:
    """Gestisce persistenza dati: profili utente e statistiche sessioni."""

    def __init__(self, data_dir: str = "data", config_path: str = "config/settings.json"):
        """Inizializza il gestore dati.

        Args:
            data_dir: cartella per i file dati
            config_path: percorso file configurazione
        """
        self.data_dir = Path(data_dir)
        self.config_path = Path(config_path)
        self.profiles_file = self.data_dir / "profiles.json"
        self.current_profile: Optional[str] = None

        self._ensure_directories()
        self._load_profiles()

    def _ensure_directories(self) -> None:
        """Crea le directory necessarie se non esistono."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_profiles(self) -> None:
        """Carica i profili utente dal file JSON."""
        self._profiles: dict = {}
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r", encoding="utf-8") as f:
                    self._profiles = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Errore caricamento profili: %s", e)
                self._profiles = {}

        if "default" not in self._profiles:
            self.create_profile("default")

    def _save_profiles(self) -> None:
        """Salva i profili su disco."""
        try:
            with open(self.profiles_file, "w", encoding="utf-8") as f:
                json.dump(self._profiles, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error("Errore salvataggio profili: %s", e)

    def get_profiles(self) -> list[str]:
        """Restituisce la lista dei nomi profilo disponibili."""
        return list(self._profiles.keys())

    def create_profile(self, name: str) -> bool:
        """Crea un nuovo profilo utente."""
        name = name.strip()
        if not name:
            return False

        if name in self._profiles:
            return False

        self._profiles[name] = {
            "created": datetime.now().isoformat(),
            "sessions_count": 0,
        }
        self._save_profiles()
        logger.info("Profilo '%s' creato", name)
        return True

    def select_profile(self, name: str) -> bool:
        """Seleziona un profilo come attivo."""
        if name not in self._profiles:
            logger.warning("Profilo '%s' non trovato", name)
            return False

        self.current_profile = name
        return True

    def delete_profile(self, name: str) -> bool:
        """Elimina un profilo e i relativi dati."""
        if name == "default":
            return False

        if name not in self._profiles:
            return False

        del self._profiles[name]
        self._save_profiles()

        csv_path = self._get_csv_path(name)
        if csv_path.exists():
            try:
                csv_path.unlink()
            except IOError as e:
                logger.error("Errore eliminazione file dati: %s", e)

        if self.current_profile == name:
            self.current_profile = "default"

        logger.info("Profilo '%s' eliminato", name)
        return True

    def _get_csv_path(self, profile_name: Optional[str] = None) -> Path:
        """Restituisce il percorso CSV per un profilo."""
        name = profile_name or self.current_profile or "default"
        return self.data_dir / f"sessions_{name}.csv"

    def save_session(
        self,
        button: str,
        press_count: int,
        session_duration: float,
        min_duration_ms: float,
        avg_duration_ms: float,
        max_duration_ms: float,
        connection_type: str,
        latency_avg: float,
        jitter: float,
        threshold_ms: float,
        threshold_successes: int,
    ) -> bool:
        """Salva i dati di una sessione nel CSV.

        Args:
            button: pulsante monitorato (o "Tutti")
            press_count: pressioni totali nella sessione
            session_duration: durata sessione in secondi
            min_duration_ms: durata minima pressione in ms
            avg_duration_ms: durata media pressione in ms
            max_duration_ms: durata massima pressione in ms
            connection_type: USB o Bluetooth
            latency_avg: latenza media polling in ms
            jitter: jitter polling in ms
            threshold_ms: soglia durata impostata in ms
            threshold_successes: pressioni sotto soglia

        Returns:
            True se il salvataggio e' riuscito
        """
        profile = self.current_profile or "default"
        csv_path = self._get_csv_path(profile)
        file_exists = csv_path.exists()

        try:
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(CSV_HEADERS)

                writer.writerow([
                    datetime.now().isoformat(),
                    profile,
                    button,
                    press_count,
                    round(session_duration, 1),
                    round(min_duration_ms, 2),
                    round(avg_duration_ms, 2),
                    round(max_duration_ms, 2),
                    connection_type,
                    round(latency_avg, 2),
                    round(jitter, 2),
                    round(threshold_ms, 1),
                    threshold_successes,
                ])

            if profile in self._profiles:
                self._profiles[profile]["sessions_count"] = (
                    self._profiles[profile].get("sessions_count", 0) + 1
                )
                self._save_profiles()

            logger.info("Sessione salvata per profilo '%s'", profile)
            return True

        except IOError as e:
            logger.error("Errore salvataggio sessione: %s", e)
            return False

    def load_sessions(self, profile_name: Optional[str] = None) -> list[dict]:
        """Carica tutte le sessioni di un profilo.

        Returns:
            lista di dict con i dati delle sessioni
        """
        csv_path = self._get_csv_path(profile_name)
        if not csv_path.exists():
            return []

        sessions = []
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for key in ["press_count", "threshold_successes"]:
                        if key in row:
                            row[key] = int(row[key])
                    for key in ["session_duration_s", "min_duration_ms",
                                "avg_duration_ms", "max_duration_ms",
                                "latency_avg_ms", "jitter_ms", "threshold_ms"]:
                        if key in row:
                            row[key] = float(row[key])
                    sessions.append(row)
        except (IOError, ValueError) as e:
            logger.error("Errore caricamento sessioni: %s", e)

        return sessions

    def export_all_data(self, output_path: str) -> bool:
        """Esporta tutti i dati di tutti i profili in un unico CSV."""
        all_sessions = []
        for profile_name in self._profiles:
            sessions = self.load_sessions(profile_name)
            all_sessions.extend(sessions)

        if not all_sessions:
            logger.warning("Nessun dato da esportare")
            return False

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(all_sessions)

            logger.info("Dati esportati in '%s' (%d sessioni)",
                        output_path, len(all_sessions))
            return True

        except IOError as e:
            logger.error("Errore export dati: %s", e)
            return False

    def load_settings(self) -> dict:
        """Carica le impostazioni dal file di configurazione."""
        defaults = {
            "soglia_durata_ms_default": 50.0,
            "intervallo_aggiornamento_ms": 50,
            "percorso_dati": "data",
            "profilo_default": "default",
        }

        if not self.config_path.exists():
            return defaults

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            for key, value in defaults.items():
                settings.setdefault(key, value)
            return settings
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Errore caricamento settings: %s", e)
            return defaults

    def save_settings(self, settings: dict) -> bool:
        """Salva le impostazioni nel file di configurazione."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error("Errore salvataggio settings: %s", e)
            return False
