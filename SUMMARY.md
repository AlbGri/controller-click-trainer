# Controller Click Trainer - Technical Summary

[🇬🇧 English](#english) | [🇮🇹 Italiano](#italiano)

---

## English

Technical and architectural overview of the project for developers and contributors.

### Project Objective

Desktop application to measure with precision the **press duration** on gaming controllers, expressed in milliseconds. Unlike traditional tools that measure clicks-per-second, this tool tracks the time between **press** and **release** of each individual press.

**Main use case**: competitive games where press duration directly influences gameplay (e.g., more or less powerful actions based on press time). Users want to train very short taps and verify if the controller "amplifies" (extends) inputs compared to their intention.

### Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| **GUI** | tkinter + ttk | Included in Python, cross-platform, lightweight |
| **Charts** | matplotlib (TkAgg backend) | Native integration with tkinter, powerful for scientific plots |
| **Controller Input** | inputs (0.5) | Event-driven library to detect press/release on Windows |
| **Numerical Calculations** | numpy | Efficiency for statistics (median, percentiles, std dev) |
| **Persistence** | CSV + JSON | Simple, human-readable, easy Excel export |
| **Build Exe** | PyInstaller | Creates standalone Windows exe without Python dependencies |
| **i18n** | Custom translations | Lightweight solution for EN/IT with runtime switching |

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GUI (tkinter)                        │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Stats Panel  │  │  Chart Panel │  │  Control Panel   │ │
│  │  (min/avg/max)│  │  (bar chart) │  │  (start/stop)    │ │
│  └───────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │ Thread-safe Queue
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ControllerMonitor (Thread)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  inputs.get_gamepad() → event loop                     │ │
│  │  - Tracks press time for each button                   │ │
│  │  - On release: calculates duration_ms, creates PressEvent │ │
│  │  - Callback → GUI queue                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │  DataManager     │  │  ControllerDiagnostics          │ │
│  │  - CSV persist   │  │  - Real-time polling rate       │ │
│  │  - JSON profiles │  │  - Latency/jitter analysis      │ │
│  │  - Settings      │  │  - Press duration stats         │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. ControllerMonitor (src/controller_monitor.py)

**Responsibility**: Input detection and press duration measurement.

**Pattern**: Separate thread with continuous event loop.

**Core logic**:
```python
# Simplified pseudo-code
button_press_times = {}  # button_code -> timestamp

for event in inputs.get_gamepad():
    if event.state == 1:  # Press
        button_press_times[event.code] = time.perf_counter()
    elif event.state == 0:  # Release
        press_time = button_press_times.pop(event.code)
        duration_ms = (time.perf_counter() - press_time) * 1000
        callback(PressEvent(button, duration_ms))
```

**Technical decisions**:
- `time.perf_counter()` for microsecond precision
- Polling rate calculated from real thread timestamps (not UI refresh)
- Thread-safe via queue to GUI

#### 2. RealtimeChart (src/visualizer.py)

**Responsibility**: Real-time bar visualization of durations.

**Pattern**: matplotlib embedded in tkinter via `FigureCanvasTkAgg`.

**Features**:
- Each bar = 1 individual press (not aggregated)
- Bar height = duration in ms
- Dynamic color: green if below threshold, red if above
- Threshold displayed as horizontal orange line
- Max 40 bars visible (sliding window)

**Optimizations**:
- `ax.clear()` + complete redraw (simple, sufficient for 50ms refresh)
- Duration labels shown only if <= 25 bars (readability)

#### 3. DataManager (src/data_manager.py)

**Responsibility**: Data persistence and profile management.

**CSV Structure** (`data/sessions_<profile>.csv`):
```
timestamp, username, button, press_count, session_duration_s,
min_duration_ms, avg_duration_ms, max_duration_ms,
connection_type, latency_avg_ms, jitter_ms,
threshold_ms, threshold_successes
```

**Profiles** (`data/profiles.json`):
```json
{
  "default": {
    "created": "2026-02-01T10:00:00",
    "sessions_count": 5
  }
}
```

**Settings** (`config/settings.json`):
- Default threshold, UI interval, theme colors, button mapping, language

#### 4. Translations (src/translations.py)

**Responsibility**: Multilanguage support (EN/IT).

**Pattern**: Dictionary-based translations with runtime language switching.

**Features**:
- Flag emoji switcher in GUI
- All UI strings translated
- Language preference saved in settings
- Dynamic UI update on language change

### Key Architectural Decisions

#### Threading Model

**Problem**: `inputs.get_gamepad()` is blocking. Running in GUI thread would freeze the interface.

**Solution**: Separate thread for monitor + thread-safe queue for communication.

```python
# In monitor thread
while self._running:
    events = inputs.get_gamepad()
    for event in events:
        press_event = process(event)
        self._callback(press_event)  # Enqueue

# In GUI thread
def _update_ui():
    with self._pending_lock:
        presses = self._pending_presses.copy()
        self._pending_presses.clear()
    for press in presses:
        update_chart(press)
    root.after(50, self._update_ui)
```

#### Inverted Threshold

The goal is to stay **below** the threshold (fast tap), not above. This is counter-intuitive compared to traditional metrics (e.g., clicks/s).

**UI Implications**:
- Green = below threshold = good
- Red = above threshold = bad
- "Successes" statistics = presses below threshold

#### Real Polling Rate vs UI Refresh

**Common mistake**: measuring polling rate from UI refresh (always ~20Hz at 50ms interval).

**Correct solution**: calculate from real input thread:
```python
poll_timestamps = deque(maxlen=2000)
poll_timestamps.append(time.perf_counter())
intervals = np.diff(poll_timestamps)
polling_rate = 1 / np.mean(intervals)
```

#### PyInstaller Frozen Support

To work as standalone exe:

**main.py**:
```python
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    os.chdir(BASE_DIR)  # Relative paths work
```

**ControllerClickTrainer.spec**:
- Includes missing conda DLLs (tcl86t, tk86t, ffi, liblzma, libbz2, libexpat)
- Bundles config/settings.json in `_internal/config/`
- Manual copy of config next to exe to allow user modifications

### Extension Points

#### New Buttons

`controller_monitor.py`:
```python
BUTTON_MAP = {
    "BTN_SOUTH": "A",
    "BTN_NEW": "Custom",  # Add here
}
```

`config/settings.json`:
```json
"controller_mappings": {
  "BTN_NEW": "Custom"
}
```

#### New Languages

`translations.py`:
```python
TRANSLATIONS = {
    "en": { ... },
    "it": { ... },
    "fr": { ... },  # Add new language
}
```

Update `get_flag_emoji()` and `get_next_language()` accordingly.

### Performance

#### Typical Metrics

| Metric | Typical Value | Notes |
|---|---|---|
| UI Refresh | 50ms (20 FPS) | Configurable in settings |
| Input Polling Rate | 125-200 Hz USB | Depends on controller |
| Memory Usage | ~80 MB | With matplotlib loaded |
| Exe Size | ~83 MB folder | Includes matplotlib, numpy, tkinter |
| Press Detection Latency | < 8ms | Limited by controller polling rate |

### License and Contributions

- **License**: MIT
- **Contributions**: Welcome via pull requests
- **Issues**: Report bugs or feature requests on GitHub Issues

For significant changes, please open an issue first for discussion.

### References

- [README.md](README.md) - Installation and usage
- [docs/usage_guide.md](docs/usage_guide.md) - Detailed user guide
- [docs/github_workflow.md](docs/github_workflow.md) - Development and release workflow
- [ControllerClickTrainer.spec](ControllerClickTrainer.spec) - PyInstaller config

**Repository**: https://github.com/AlbGri/controller-click-trainer

---

## Italiano

Panoramica tecnica e architetturale del progetto per sviluppatori e contributori.

### Obiettivo del Progetto

Applicazione desktop per misurare con precisione la **durata delle pressioni** sui controller gaming, espressa in millisecondi. A differenza dei tool tradizionali che misurano click-per-secondo, questo tool traccia il tempo tra **press** e **release** di ogni singola pressione.

**Caso d'uso principale**: giochi competitivi dove la durata della pressione influenza direttamente il gameplay (es. azioni più o meno potenti in base al tempo di pressione). Gli utenti vogliono allenare tap brevissimi e verificare se il controller "amplifica" (allunga) gli input rispetto alla loro intenzione.

### Stack Tecnologico

| Componente | Tecnologia | Motivazione |
|---|---|---|
| **GUI** | tkinter + ttk | Incluso in Python, cross-platform, lightweight |
| **Grafici** | matplotlib (backend TkAgg) | Integrazione nativa con tkinter, potente per grafici scientifici |
| **Input Controller** | inputs (0.5) | Libreria event-driven per rilevare press/release su Windows |
| **Calcoli Numerici** | numpy | Efficienza per statistiche (mediana, percentili, std dev) |
| **Persistenza** | CSV + JSON | Semplice, human-readable, facile export Excel |
| **Build Exe** | PyInstaller | Crea standalone Windows exe senza dipendenze Python |
| **i18n** | Traduzioni custom | Soluzione leggera per EN/IT con cambio runtime |

### Architettura High-Level

```
┌─────────────────────────────────────────────────────────────┐
│                        GUI (tkinter)                        │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Stats Panel  │  │  Chart Panel │  │  Control Panel   │ │
│  │  (min/avg/max)│  │  (bar chart) │  │  (start/stop)    │ │
│  └───────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │ Thread-safe Queue
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ControllerMonitor (Thread)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  inputs.get_gamepad() → event loop                     │ │
│  │  - Traccia press time per ogni pulsante                │ │
│  │  - Al release: calcola duration_ms, crea PressEvent    │ │
│  │  - Callback → GUI queue                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │  DataManager     │  │  ControllerDiagnostics          │ │
│  │  - CSV persist   │  │  - Polling rate real-time       │ │
│  │  - Profili JSON  │  │  - Analisi latency/jitter       │ │
│  │  - Settings      │  │  - Statistiche durate pressioni │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Componenti Chiave

#### 1. ControllerMonitor (src/controller_monitor.py)

**Responsabilità**: Rilevamento input e misurazione durata pressioni.

**Pattern**: Thread separato con event loop continuo.

**Logica core**:
```python
# Pseudo-codice semplificato
button_press_times = {}  # button_code -> timestamp

for event in inputs.get_gamepad():
    if event.state == 1:  # Press
        button_press_times[event.code] = time.perf_counter()
    elif event.state == 0:  # Release
        press_time = button_press_times.pop(event.code)
        duration_ms = (time.perf_counter() - press_time) * 1000
        callback(PressEvent(button, duration_ms))
```

**Decisioni tecniche**:
- `time.perf_counter()` per precisione microsecondo
- Polling rate calcolato da timestamps reali del thread (non da UI refresh)
- Thread-safe tramite queue verso GUI

#### 2. RealtimeChart (src/visualizer.py)

**Responsabilità**: Visualizzazione barre real-time delle durate.

**Pattern**: matplotlib embedded in tkinter via `FigureCanvasTkAgg`.

**Peculiarità**:
- Ogni barra = 1 pressione singola (non aggregata)
- Altezza barra = durata in ms
- Colore dinamico: verde se sotto soglia, rosso se sopra
- Soglia visualizzata come linea orizzontale arancione
- Max 40 barre visibili (sliding window)

**Ottimizzazioni**:
- `ax.clear()` + redraw completo (semplice, sufficiente per 50ms refresh)
- Labels durata mostrate solo se <= 25 barre (leggibilità)

#### 3. DataManager (src/data_manager.py)

**Responsabilità**: Persistenza dati e gestione profili.

**Struttura CSV** (`data/sessions_<profile>.csv`):
```
timestamp, username, button, press_count, session_duration_s,
min_duration_ms, avg_duration_ms, max_duration_ms,
connection_type, latency_avg_ms, jitter_ms,
threshold_ms, threshold_successes
```

**Profili** (`data/profiles.json`):
```json
{
  "default": {
    "created": "2026-02-01T10:00:00",
    "sessions_count": 5
  }
}
```

**Settings** (`config/settings.json`):
- Soglia default, intervallo UI, colori tema, mapping pulsanti, lingua

#### 4. Translations (src/translations.py)

**Responsabilità**: Supporto multilingua (EN/IT).

**Pattern**: Traduzioni basate su dizionari con cambio lingua runtime.

**Caratteristiche**:
- Selettore bandiera emoji nella GUI
- Tutte le stringhe UI tradotte
- Preferenza lingua salvata in settings
- Aggiornamento UI dinamico al cambio lingua

### Decisioni Architetturali Chiave

#### Threading Model

**Problema**: `inputs.get_gamepad()` è bloccante. Se eseguito nel thread GUI, freezerebbe l'interfaccia.

**Soluzione**: Thread separato per monitor + queue thread-safe per comunicazione.

```python
# Nel thread monitor
while self._running:
    events = inputs.get_gamepad()
    for event in events:
        press_event = process(event)
        self._callback(press_event)  # Accoda

# Nel thread GUI
def _update_ui():
    with self._pending_lock:
        presses = self._pending_presses.copy()
        self._pending_presses.clear()
    for press in presses:
        update_chart(press)
    root.after(50, self._update_ui)
```

#### Soglia Invertita

L'obiettivo è stare **sotto** la soglia (tap rapido), non sopra. Questo è contro-intuitivo rispetto a metriche tradizionali (es. click/s).

**Implicazioni UI**:
- Verde = sotto soglia = buono
- Rosso = sopra soglia = male
- Statistiche "successi" = pressioni sotto soglia

#### Polling Rate Reale vs UI Refresh

**Errore comune**: misurare polling rate dal refresh UI (sempre ~20Hz a 50ms intervallo).

**Soluzione corretta**: calcolare dal thread input reale:
```python
poll_timestamps = deque(maxlen=2000)
poll_timestamps.append(time.perf_counter())
intervals = np.diff(poll_timestamps)
polling_rate = 1 / np.mean(intervals)
```

#### PyInstaller Frozen Support

Per funzionare come exe standalone:

**main.py**:
```python
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    os.chdir(BASE_DIR)  # Percorsi relativi funzionano
```

**ControllerClickTrainer.spec**:
- Include DLL conda mancanti (tcl86t, tk86t, ffi, liblzma, libbz2, libexpat)
- Bundle config/settings.json in `_internal/config/`
- Copia manuale config accanto exe per permettere modifiche utente

### Punti di Estensione

#### Nuovi Pulsanti

`controller_monitor.py`:
```python
BUTTON_MAP = {
    "BTN_SOUTH": "A",
    "BTN_NEW": "Custom",  # Aggiungi qui
}
```

`config/settings.json`:
```json
"controller_mappings": {
  "BTN_NEW": "Custom"
}
```

#### Nuove Lingue

`translations.py`:
```python
TRANSLATIONS = {
    "en": { ... },
    "it": { ... },
    "fr": { ... },  # Aggiungi nuova lingua
}
```

Aggiorna `get_flag_emoji()` e `get_next_language()` di conseguenza.

### Performance

#### Metriche Tipiche

| Metrica | Valore Tipico | Note |
|---|---|---|
| UI Refresh | 50ms (20 FPS) | Configurabile in settings |
| Polling Rate Input | 125-200 Hz USB | Dipende da controller |
| Memoria Uso | ~80 MB | Con matplotlib caricato |
| Exe Size | ~83 MB cartella | Include matplotlib, numpy, tkinter |
| Latency Press Detection | < 8ms | Limitato da polling rate controller |

### Licenza e Contributi

- **Licenza**: MIT
- **Contributi**: Benvenuti via pull request
- **Issues**: Segnalare bug o feature request su GitHub Issues

Per modifiche significative, aprire prima un issue per discussione.

### Riferimenti

- [README.md](README.md) - Installazione e uso
- [docs/usage_guide.md](docs/usage_guide.md) - Guida dettagliata utente
- [docs/github_workflow.md](docs/github_workflow.md) - Workflow sviluppo e release
- [ControllerClickTrainer.spec](ControllerClickTrainer.spec) - Config PyInstaller

**Repository**: https://github.com/AlbGri/controller-click-trainer
