# Controller Click Trainer - Technical Summary

Panoramica tecnica e architetturale del progetto per sviluppatori e contributori.

---

## Obiettivo del Progetto

Applicazione desktop per misurare con precisione la **durata delle pressioni** sui controller gaming, espressa in millisecondi. A differenza dei tool tradizionali che misurano click-per-secondo, questo tool traccia il tempo tra **press** e **release** di ogni singola pressione.

**Caso d'uso principale**: giochi competitivi dove la durata della pressione influenza direttamente il gameplay (es. azioni piu' o meno potenti in base al tempo di pressione). Gli utenti vogliono allenare tap brevissimi e verificare se il controller "amplifica" (allunga) gli input rispetto alla loro intenzione.

---

## Stack Tecnologico

| Componente | Tecnologia | Motivazione |
|---|---|---|
| **GUI** | tkinter + ttk | Incluso in Python, cross-platform, lightweight |
| **Grafici** | matplotlib (backend TkAgg) | Integrazione nativa con tkinter, potente per grafici scientifici |
| **Input Controller** | inputs (0.5) | Libreria event-driven per rilevare press/release su Windows |
| **Calcoli Numerici** | numpy | Efficienza per statistiche (mediana, percentili, std dev) |
| **Persistenza** | CSV + JSON | Semplice, human-readable, facile export Excel |
| **Build Exe** | PyInstaller | Crea standalone Windows exe senza dipendenze Python |

---

## Architettura High-Level

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
│  │  - Profili JSON  │  │  - Latency/jitter analysis      │ │
│  │  - Settings      │  │  - Press duration stats         │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Componenti Chiave

### 1. ControllerMonitor (src/controller_monitor.py)

**Responsabilita**: Rilevamento input e misurazione durata pressioni.

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

### 2. RealtimeChart (src/visualizer.py)

**Responsabilita**: Visualizzazione barre real-time delle durate.

**Pattern**: matplotlib embedded in tkinter via `FigureCanvasTkAgg`.

**Peculiarita**:
- Ogni barra = 1 pressione singola (non aggregata)
- Altezza barra = durata in ms
- Colore dinamico: verde se sotto soglia, rosso se sopra
- Soglia visualizzata come linea orizzontale arancione
- Max 40 barre visibili (sliding window)

**Ottimizzazioni**:
- `ax.clear()` + redraw completo (semplice, sufficiente per 50ms refresh)
- Labels durate mostrate solo se <= 25 barre (leggibilita)

### 3. DataManager (src/data_manager.py)

**Responsabilita**: Persistenza dati e gestione profili.

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
  },
  "competitive": { ... }
}
```

**Settings** (`config/settings.json`):
- Soglia default, intervallo UI, colori tema, mapping pulsanti

### 4. ControllerDiagnostics (src/diagnostics.py)

**Responsabilita**: Valutazione qualita connessione controller.

**Metriche**:
- **Polling rate**: Hz reale dal thread input (200Hz USB tipico, 60-125Hz Bluetooth)
- **Latency**: intervallo medio tra poll consecutivi
- **Jitter**: deviazione standard latency (stabilita connessione)
- **Quality**: classificazione Ottima/Buona/Discreta/Scarsa

**Analisi durate pressioni**:
- Mediana, percentili (10°, 90°), deviazione standard
- % pressioni sotto 50ms, sotto 100ms
- Fast-tap consistency (coefficient of variation)

---

## Decisioni Architetturali Chiave

### Threading Model

**Problema**: `inputs.get_gamepad()` e' bloccante. Se eseguito nel thread GUI, freezerebbe l'interfaccia.

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

### Soglia Invertita

L'obiettivo e' stare **sotto** la soglia (tap rapido), non sopra. Questo e' contro-intuitivo rispetto a metriche tradizionali (es. click/s).

**Implicazioni UI**:
- Verde = sotto soglia = buono
- Rosso = sopra soglia = male
- Statistiche "successi" = pressioni sotto soglia

### Polling Rate Reale vs UI Refresh

**Errore comune**: misurare polling rate dal refresh UI (sempre ~20Hz a 50ms intervallo).

**Soluzione corretta**: calcolare dal thread input reale:
```python
poll_timestamps = deque(maxlen=2000)
poll_timestamps.append(time.perf_counter())
intervals = np.diff(poll_timestamps)
polling_rate = 1 / np.mean(intervals)
```

### PyInstaller Frozen Support

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

---

## Punti di Estensione

### Nuovi Pulsanti

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

### Nuove Metriche Diagnostiche

`diagnostics.py` → `ControllerDiagnostics.analyze_press_durations()`:
```python
def analyze_press_durations(self, durations_ms: list[float]) -> dict:
    # Aggiungi nuove metriche (es. kurtosis, skewness)
    return {
        "median_ms": ...,
        "kurtosis": stats.kurtosis(durations_ms),  # Nuovo
    }
```

### Nuovi Grafici Storici

`visualizer.py` → `HistoryVisualizer`:
```python
def plot_custom_metric(self, sessions: list[dict]) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    # Implementa grafico custom
    return fig
```

`gui.py` → `_show_history_window()`:
```python
notebook.add(viz.plot_custom_metric(sessions), text="Custom")
```

### Export Formati Alternativi

`data_manager.py`:
```python
def export_to_excel(self, output_path: str) -> bool:
    import pandas as pd
    sessions = self.load_sessions()
    df = pd.DataFrame(sessions)
    df.to_excel(output_path, index=False)
```

---

## Testing e Troubleshooting

### Test Manuale Polling Rate

Verifica che diagnostica mostri polling rate reale, non UI refresh:
1. Avvia app
2. Premi un pulsante qualsiasi
3. Controlla diagnostica in basso a sinistra
4. Dovrebbe mostrare 100-200 Hz (USB) o 60-125 Hz (Bluetooth)
5. Se mostra ~20 Hz → bug: sta misurando UI refresh invece di input thread

### Debug Thread Safety

Se l'app crasha o pressioni duplicate:
- Verifica `_pending_lock` sia acquisito in `_on_press_from_thread` e `_update_ui`
- Verifica `_pending_presses.copy()` e `.clear()` siano atomici

### PyInstaller DLL Mancanti

Se exe crasha all'avvio:
1. Esegui exe da cmd: `ControllerClickTrainer.exe`
2. Leggi errore (es. "ImportError: DLL load failed: tcl86t.dll")
3. Aggiungi DLL in `ControllerClickTrainer.spec` → `binaries`
4. Rebuild: `pyinstaller ControllerClickTrainer.spec --noconfirm`

---

## Performance

### Metriche Tipiche

| Metrica | Valore Tipico | Note |
|---|---|---|
| UI Refresh | 50ms (20 FPS) | Configurabile in settings |
| Polling Rate Input | 125-200 Hz USB | Dipende da controller |
| Memoria Uso | ~80 MB | Con matplotlib caricato |
| Exe Size | ~83 MB cartella | Include matplotlib, numpy, tkinter |
| Latency Press Detection | < 8ms | Limitato da polling rate controller |

### Ottimizzazioni Future

- **Chart rendering**: Usare `blit` di matplotlib invece di redraw completo (guadagno ~10ms)
- **Deque limitato**: `_pending_presses` non ha limite → rischio memory leak se callback troppo frequenti
- **Numpy vectorization**: Alcune loop in diagnostics potrebbero essere vettorizzate

---

## Licenza e Contributi

- **Licenza**: MIT
- **Contributi**: Benvenuti via pull request
- **Issues**: Segnalare bug o feature request su GitHub Issues

Per modifiche significative, aprire prima un issue per discussione.

---

## Riferimenti

- [README.md](README.md) - Installazione e uso
- [docs/usage_guide.md](docs/usage_guide.md) - Guida dettagliata utente
- [docs/github_workflow.md](docs/github_workflow.md) - Workflow sviluppo e release
- [ControllerClickTrainer.spec](ControllerClickTrainer.spec) - Config PyInstaller

**Repository**: https://github.com/AlbGri/controller-click-trainer
