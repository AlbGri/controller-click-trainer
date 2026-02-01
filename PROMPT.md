# PROMPT PER AI ASSISTANT

---

## PARTE 1 - CONFIGURAZIONE AMBIENTE (Universale - da riutilizzare in ogni progetto)

### Contesto sistema sviluppatore

Sto lavorando su **Windows 11** con la seguente configurazione:

- **Python**: NON e' installato a livello di sistema. Il comando `python` nel terminale punta allo stub Microsoft Store e non funziona.
- **Gestore ambienti**: Uso **Miniconda**, installato in `C:\ProgramData\miniconda3` (installazione di sistema, read-only).
- **Conda version**: 25.1.1 (o successiva)
- **Solver**: libmamba
- **Directory environments**: `C:\Users\Alberto\.conda\envs\`
- **pip e python** funzionano SOLO dentro un conda environment attivato.
- **VS Code**: e' il mio IDE principale. L'interprete Python va selezionato dall'environment conda del progetto.

### Istruzioni per la verifica ambiente

Prima di sviluppare qualsiasi progetto Python, segui questa procedura:

1. **NON eseguire** `python --version` o `pip --version` direttamente: falliranno perche' Python non e' nel PATH di sistema.

2. **Verifica conda** con:
   ```
   powershell.exe -Command "& 'C:\ProgramData\miniconda3\Scripts\conda.exe' --version"
   ```

3. **Lista environment esistenti**:
   ```
   powershell.exe -Command "& 'C:\ProgramData\miniconda3\Scripts\conda.exe' env list"
   ```

4. **Crea un nuovo environment dedicato** per il progetto (nome che richiami il progetto):
   ```
   powershell.exe -Command "& 'C:\ProgramData\miniconda3\Scripts\conda.exe' create -n NOME_ENV python=3.12 -y"
   ```

5. **Installa dipendenze** usando il python dell'environment:
   ```
   powershell.exe -Command "& 'C:\Users\Alberto\.conda\envs\NOME_ENV\python.exe' -m pip install PACCHETTO"
   ```

6. **Esegui script** usando il python dell'environment:
   ```
   powershell.exe -Command "& 'C:\Users\Alberto\.conda\envs\NOME_ENV\python.exe' script.py"
   ```

### Note importanti

- Se il terminale Claude Code usa bash (Git Bash/WSL), i comandi Windows con backslash non funzionano. Usa sempre `powershell.exe -Command "..."` come wrapper.
- I percorsi conda dell'utente sono: `C:\Users\Alberto\.conda\envs\`
- Ogni progetto deve avere il **proprio environment isolato**.
- Il file `requirements.txt` deve essere presente in ogni progetto per riproducibilita.
- L'utente attivera' l'environment nel terminale VS Code con `conda activate NOME_ENV` prima di lavorare interattivamente.

### Setup VS Code per il progetto

Dopo aver creato l'environment, l'utente dovra':
1. Aprire VS Code nel progetto
2. `Ctrl + Shift + P` > "Python: Select Interpreter"
3. Selezionare l'environment conda del progetto
4. Il terminale integrato usera' automaticamente quell'environment se configurato con:
   ```
   "python.condaPath": "C:\\ProgramData\\miniconda3\\Scripts\\conda.exe"
   ```

---

## PARTE 2 - PROMPT PROGETTO: Controller Click Trainer

### Descrizione

Applicazione desktop Python per monitorare la **durata delle pressioni** sui controller gaming. Misura in millisecondi quanto tempo un tasto resta premuto (dal press al release), con l'obiettivo di allenarsi a fare pressioni il piu' brevi possibile.

Caso d'uso principale: in giochi come Rocket League, la durata della pressione del tasto salto determina l'altezza del salto. L'utente vuole allenare tap brevissimi e verificare che il controller non stia "allungando" gli input.

### Environment conda

- **Nome**: `click-trainer`
- **Python**: 3.12
- **Percorso**: `C:\Users\Alberto\.conda\envs\click-trainer`
- **Dipendenze**: matplotlib, numpy, inputs (vedi requirements.txt)

### Struttura progetto

```
controller-click-trainer/
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point
│   ├── controller_monitor.py  # Traccia press/release, calcola durata ms
│   ├── data_manager.py        # Gestione dati, profili, CSV
│   ├── diagnostics.py         # Polling rate reale, latenza, jitter, analisi durate
│   ├── visualizer.py          # Grafici a barre real-time + storici
│   └── gui.py                 # Interfaccia grafica tkinter
├── config/
│   └── settings.json          # Configurazione (soglia ms, colori, mapping)
├── data/                      # Sessioni salvate (CSV per profilo)
├── docs/
│   └── usage_guide.md
├── requirements.txt
├── .gitignore
├── LICENSE (MIT)
└── README.md
```

### Architettura

- **ControllerMonitor**: thread separato per lettura input, traccia timestamp press e release per ogni pulsante, calcola durata in ms, callback alla GUI al completamento di ogni pressione
- **DataManager**: persistenza CSV con colonne durata (min/avg/max), profili JSON, settings
- **ControllerDiagnostics**: valutazione qualita connessione basata su polling rate reale dal thread input (non dal refresh UI), analisi statistica delle durate pressioni (mediana, percentili, deviazione standard)
- **RealtimeChart**: grafico a barre matplotlib embedded in tkinter. Ogni barra = 1 pressione, altezza = durata ms, verde se sotto soglia, rosso se sopra
- **HistoryVisualizer**: grafici statici (progressi durate, distribuzione, diagnostica latenza)
- **App (gui.py)**: orchestratore GUI con coda thread-safe per pressioni dal monitor, log testuale pressioni, aggiornamento UI tramite `root.after()`

### Logica chiave

- La **soglia e' invertita**: l'obiettivo e' stare SOTTO il valore (es. sotto 50ms = tap veloce)
- **Verde = buono** (pressione breve, sotto soglia), **Rosso = male** (pressione lunga, sopra soglia)
- La pressione viene registrata solo al **release** (serve il ciclo completo press -> release)
- Il **polling rate** viene calcolato dal thread di input reale, non dal refresh della GUI
- I dati CSV salvano: min_duration_ms, avg_duration_ms, max_duration_ms per sessione

### Convenzioni codice

- PEP 8, type hints, docstrings, commenti in italiano
- Nessun emoji nel codice
- Logging con modulo `logging`
- Gestione errori con try-except mirati

### Come eseguire

```bash
conda activate click-trainer
cd c:\Alberto\Coding\controller-click-trainer
python src/main.py
```

### Come estendere

- Nuovi pulsanti: modifica `BUTTON_MAP` / `TRIGGER_MAP` in `controller_monitor.py`
- Colori/soglie: modifica `config/settings.json`
- Nuovi grafici: estendi `HistoryVisualizer` in `visualizer.py`
- Nuove metriche: estendi `ControllerDiagnostics.analyze_press_durations()` in `diagnostics.py`
