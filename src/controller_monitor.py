"""Modulo per il monitoraggio input del controller gaming.

Gestisce rilevamento controller Xbox (nativi e DS4Windows),
monitoraggio input real-time con focus sulla DURATA delle pressioni.
Traccia press/release per misurare quanto tempo un tasto resta premuto.
"""

import threading
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Callable

try:
    import inputs
except ImportError:
    inputs = None

logger = logging.getLogger(__name__)


@dataclass
class PressEvent:
    """Singola pressione completa (press + release)."""
    button: str
    press_time: float
    release_time: float
    duration_ms: float


@dataclass
class SessionStats:
    """Statistiche della sessione corrente."""
    start_time: float = 0.0
    total_presses: int = 0
    presses_per_button: dict = field(default_factory=dict)
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    last_duration_ms: float = 0.0
    threshold_successes: int = 0
    below_threshold: bool = False
    durations_history: list = field(default_factory=list)


class ControllerMonitor:
    """Gestisce il monitoraggio degli input del controller.

    Rileva controller Xbox/compatibili, traccia press e release di ogni
    pulsante, misura la durata di ogni pressione in millisecondi.
    """

    # Mapping pulsanti inputs -> nomi leggibili
    BUTTON_MAP = {
        "BTN_SOUTH": "A",
        "BTN_EAST": "B",
        "BTN_WEST": "X",
        "BTN_NORTH": "Y",
        "BTN_TL": "LB",
        "BTN_TR": "RB",
        "BTN_THUMBL": "LS",
        "BTN_THUMBR": "RS",
        "BTN_START": "Start",
        "BTN_SELECT": "Back",
    }

    # Trigger analogici (valore 0-255)
    TRIGGER_MAP = {
        "ABS_Z": "LT",
        "ABS_RZ": "RT",
    }

    # D-Pad
    DPAD_MAP = {
        "ABS_HAT0X": "D-Pad X",
        "ABS_HAT0Y": "D-Pad Y",
    }

    def __init__(self, threshold_ms: float = 50.0):
        """Inizializza il monitor.

        Args:
            threshold_ms: soglia durata in ms - l'obiettivo e' stare SOTTO
        """
        self.threshold_ms = threshold_ms

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Stato corrente di ogni pulsante (timestamp press o None)
        self._button_press_times: dict[str, float] = {}
        # Storico pressioni complete
        self._press_log: list[PressEvent] = []
        # Timestamps polling reale dal thread input
        self._poll_timestamps: deque = deque(maxlen=2000)
        # Callback per notifiche alla GUI
        self._on_press_complete: Optional[Callable] = None

        self.stats = SessionStats()
        self.controller_name: str = "Nessun controller"
        self.connection_type: str = "Sconosciuto"
        self._gamepad = None

        # Soglia trigger analogici per considerarli "premuti"
        self._trigger_threshold = 128
        self._trigger_states: dict[str, bool] = {}
        # Stato D-Pad per tracciare release
        self._dpad_states: dict[str, bool] = {}

        # Pulsante attualmente monitorato (None = tutti)
        self.monitored_button: Optional[str] = None

    def detect_controller(self) -> bool:
        """Rileva il primo controller disponibile.

        Returns:
            True se un controller e' stato trovato
        """
        if inputs is None:
            logger.error("Libreria 'inputs' non installata")
            return False

        try:
            gamepads = inputs.devices.gamepads
            if not gamepads:
                logger.warning("Nessun controller rilevato")
                self.controller_name = "Nessun controller"
                return False

            self._gamepad = gamepads[0]
            self.controller_name = self._gamepad.name or "Controller sconosciuto"
            self._detect_connection_type()

            logger.info("Controller rilevato: %s (%s)",
                        self.controller_name, self.connection_type)
            return True

        except Exception as e:
            logger.error("Errore rilevamento controller: %s", e)
            return False

    def _detect_connection_type(self) -> None:
        """Tenta di determinare il tipo di connessione (USB/Bluetooth)."""
        if self._gamepad is None:
            return

        name_lower = self.controller_name.lower()
        if "bluetooth" in name_lower or "wireless" in name_lower:
            self.connection_type = "Bluetooth"
        else:
            self.connection_type = "USB"

    def set_callback(self, on_press_complete: Optional[Callable] = None) -> None:
        """Imposta callback per pressione completata (press+release).

        Args:
            on_press_complete: chiamata con PressEvent ad ogni rilascio pulsante
        """
        self._on_press_complete = on_press_complete

    def set_threshold(self, value_ms: float) -> None:
        """Aggiorna la soglia durata target in ms."""
        self.threshold_ms = max(1.0, value_ms)

    def set_monitored_button(self, button: Optional[str]) -> None:
        """Imposta il pulsante specifico da monitorare.

        Args:
            button: nome pulsante (es. "A", "B") o None per tutti
        """
        self.monitored_button = button

    def start(self) -> bool:
        """Avvia il monitoraggio in un thread separato.

        Returns:
            True se il monitoraggio e' partito
        """
        if self._running:
            return True

        if not self.detect_controller():
            return False

        self._running = True
        self.stats = SessionStats(start_time=time.time())
        self._button_press_times.clear()
        self._press_log.clear()
        self._poll_timestamps.clear()
        self._trigger_states.clear()
        self._dpad_states.clear()

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        logger.info("Monitoraggio avviato")
        return True

    def stop(self) -> SessionStats:
        """Ferma il monitoraggio e restituisce le statistiche.

        Returns:
            statistiche della sessione appena conclusa
        """
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info("Monitoraggio fermato - Pressioni totali: %d",
                     self.stats.total_presses)
        return self.stats

    @property
    def is_running(self) -> bool:
        return self._running

    def _monitor_loop(self) -> None:
        """Loop principale di monitoraggio (eseguito in thread separato)."""
        while self._running:
            try:
                events = inputs.get_gamepad()
                now = time.time()
                self._poll_timestamps.append(now)

                for event in events:
                    self._process_event(event, now)

            except inputs.UnpluggedError:
                logger.warning("Controller scollegato")
                self._running = False
                break
            except Exception as e:
                logger.error("Errore lettura input: %s", e)
                time.sleep(0.01)

    def _process_event(self, event, timestamp: float) -> None:
        """Processa un singolo evento input, tracciando press e release.

        Args:
            event: evento dalla libreria inputs
            timestamp: momento della ricezione
        """
        code = event.code
        state = event.state

        button_name = None
        is_press = False
        is_release = False

        # Pulsanti digitali: state 1 = press, state 0 = release
        if code in self.BUTTON_MAP:
            button_name = self.BUTTON_MAP[code]
            if state == 1:
                is_press = True
            elif state == 0:
                is_release = True

        # Trigger analogici
        elif code in self.TRIGGER_MAP:
            trigger_name = self.TRIGGER_MAP[code]
            was_pressed = self._trigger_states.get(code, False)
            is_pressed = state > self._trigger_threshold

            if is_pressed and not was_pressed:
                button_name = trigger_name
                is_press = True
            elif not is_pressed and was_pressed:
                button_name = trigger_name
                is_release = True

            self._trigger_states[code] = is_pressed

        # D-Pad
        elif code in self.DPAD_MAP:
            dpad_name = self.DPAD_MAP[code]
            was_pressed = self._dpad_states.get(code, False)
            is_pressed = state != 0

            if is_pressed and not was_pressed:
                button_name = dpad_name
                is_press = True
            elif not is_pressed and was_pressed:
                button_name = dpad_name
                is_release = True

            self._dpad_states[code] = is_pressed

        if button_name is None:
            return

        # Filtro per pulsante monitorato
        if self.monitored_button and button_name != self.monitored_button:
            return

        if is_press:
            self._button_press_times[button_name] = timestamp

        elif is_release:
            press_time = self._button_press_times.pop(button_name, None)
            if press_time is not None:
                duration_ms = (timestamp - press_time) * 1000.0
                self._register_press(button_name, press_time, timestamp, duration_ms)

    def _register_press(
        self, button: str, press_time: float,
        release_time: float, duration_ms: float
    ) -> None:
        """Registra una pressione completa e aggiorna le statistiche.

        Args:
            button: nome del pulsante
            press_time: timestamp della pressione
            release_time: timestamp del rilascio
            duration_ms: durata in millisecondi
        """
        event = PressEvent(
            button=button,
            press_time=press_time,
            release_time=release_time,
            duration_ms=round(duration_ms, 2),
        )

        with self._lock:
            self._press_log.append(event)
            self._update_stats(event)

        if self._on_press_complete:
            try:
                self._on_press_complete(event)
            except Exception:
                pass

    def _update_stats(self, event: PressEvent) -> None:
        """Aggiorna statistiche dopo una pressione completa.

        Args:
            event: evento pressione completata
        """
        d = event.duration_ms
        self.stats.total_presses += 1
        self.stats.last_duration_ms = d
        self.stats.presses_per_button[event.button] = (
            self.stats.presses_per_button.get(event.button, 0) + 1
        )

        if d < self.stats.min_duration_ms:
            self.stats.min_duration_ms = d
        if d > self.stats.max_duration_ms:
            self.stats.max_duration_ms = d

        # Verifica soglia (successo = durata SOTTO la soglia)
        was_below = self.stats.below_threshold
        self.stats.below_threshold = d <= self.threshold_ms

        if self.stats.below_threshold:
            self.stats.threshold_successes += 1

        # Salva nello storico
        self.stats.durations_history.append(
            (event.release_time, d, event.button)
        )

    def get_recent_presses(self, last_n: int = 50) -> list[PressEvent]:
        """Restituisce le ultime N pressioni.

        Args:
            last_n: numero di pressioni da restituire
        """
        with self._lock:
            return list(self._press_log[-last_n:])

    def get_press_log(self) -> list[PressEvent]:
        """Restituisce il log completo delle pressioni."""
        with self._lock:
            return list(self._press_log)

    def get_avg_duration(self) -> float:
        """Restituisce la durata media delle pressioni in ms."""
        with self._lock:
            if not self._press_log:
                return 0.0
            total = sum(p.duration_ms for p in self._press_log)
            return round(total / len(self._press_log), 2)

    def get_polling_rate(self) -> float:
        """Calcola il polling rate effettivo in Hz dal thread di input."""
        if len(self._poll_timestamps) < 10:
            return 0.0

        timestamps = list(self._poll_timestamps)
        # Usa solo gli ultimi 200 campioni per un valore stabile
        recent = timestamps[-200:]
        if len(recent) < 2:
            return 0.0

        total_time = recent[-1] - recent[0]
        if total_time > 0:
            return (len(recent) - 1) / total_time
        return 0.0

    def get_latency_stats(self) -> dict:
        """Calcola statistiche di latenza dagli intervalli tra poll.

        Returns:
            dict con avg, min, max, jitter in ms
        """
        if len(self._poll_timestamps) < 10:
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "jitter": 0.0}

        timestamps = list(self._poll_timestamps)
        recent = timestamps[-200:]
        intervals_ms = [
            (recent[i] - recent[i - 1]) * 1000
            for i in range(1, len(recent))
        ]

        avg = sum(intervals_ms) / len(intervals_ms)
        min_val = min(intervals_ms)
        max_val = max(intervals_ms)
        variance = sum((x - avg) ** 2 for x in intervals_ms) / len(intervals_ms)
        jitter = variance ** 0.5

        return {
            "avg": round(avg, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "jitter": round(jitter, 2),
        }

    def get_session_duration(self) -> float:
        """Restituisce la durata della sessione in secondi."""
        if self.stats.start_time == 0:
            return 0.0
        return time.time() - self.stats.start_time

    def get_available_buttons(self) -> list[str]:
        """Restituisce la lista di nomi pulsanti disponibili."""
        all_buttons = list(self.BUTTON_MAP.values())
        all_buttons.extend(self.TRIGGER_MAP.values())
        all_buttons.extend(self.DPAD_MAP.values())
        return all_buttons
