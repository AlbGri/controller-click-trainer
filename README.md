# Controller Click Trainer

Applicazione desktop per monitorare e allenare la **durata delle pressioni** sui controller gaming (Xbox, DS4Windows).
Misura in millisecondi quanto tempo un tasto resta premuto, fornisce feedback visivo rispetto a una soglia configurabile e salva le statistiche per tracciare i progressi.

## A cosa serve

In molti giochi competitivi, la durata della pressione di un tasto influenza direttamente il gameplay (es. azioni piu' o meno potenti in base al tempo di pressione). Questo tool ti aiuta a:

- **Misurare** la durata esatta di ogni singola pressione in ms
- **Allenare** i tap rapidi: l'obiettivo e' stare **sotto** una soglia target
- **Verificare** se il controller sta "allungando" gli input rispetto alla tua intenzione
- **Confrontare** le prestazioni USB vs Bluetooth
- **Tracciare** i progressi nel tempo

## Funzionalita

- **Durata ogni pressione**: registra press e release, calcola durata in ms
- **Grafico a barre real-time**: ogni barra = 1 pressione, verde se sotto soglia, rosso se sopra
- **Soglia invertita**: l'obiettivo e' stare **sotto** il target (es. sotto 50ms = tap veloce)
- **Log pressioni**: lista scrollabile con durata e pulsante di ogni pressione
- **Tutti i pulsanti**: A, B, X, Y, LB, RB, LT, RT, LS, RS, D-Pad, Start, Back
- **Profili utente**: gestione multipla con CSV separati
- **Grafici storici**: progressi durate, distribuzione, diagnostica
- **Diagnostica controller**: polling rate reale, latenza, jitter, qualita connessione

## Requisiti Sistema

- Windows 10/11
- Controller Xbox o compatibile (anche DS4Windows con emulazione Xbox)

## Installazione

### Opzione 1: Download Exe Standalone (consigliato per utenti finali)

**Nessuna installazione Python richiesta!**

1. Vai alla pagina [Releases](https://github.com/AlbGri/controller-click-trainer/releases)
2. Scarica l'ultima versione: `ControllerClickTrainer-vX.X.X-windows.zip`
3. Estrai il file ZIP in una cartella
4. Esegui `ControllerClickTrainer.exe`

Il file `config\settings.json` accanto all'exe puo' essere modificato per personalizzare colori e soglie.

#### ⚠️ Windows SmartScreen Warning

Al primo avvio, Windows Defender SmartScreen potrebbe mostrare un avviso "App non riconosciuta" o "Windows ha protetto il PC".

**Questo e' normale per applicazioni open source non firmate digitalmente.**

**Come procedere**:
1. Clicca su **"Ulteriori informazioni"** (o "More info")
2. Clicca su **"Esegui comunque"** (o "Run anyway")
3. L'applicazione si avviera' normalmente

**Perche' succede?**
- L'exe non ha una firma digitale (i certificati costano $200-400/anno)
- Windows blocca per precauzione tutti gli exe non firmati scaricati da Internet

**E' sicuro?**
- ✅ Codice completamente open source e ispezionabile
- ✅ Nessuna connessione Internet durante l'uso
- ✅ Nessun dato inviato a server esterni
- ✅ Puoi compilare l'exe tu stesso dal sorgente (vedi [docs/github_workflow.md](docs/github_workflow.md))

### Opzione 2: Esecuzione da Sorgente (per sviluppatori)

**Requisiti**: Python 3.8+ (consigliato 3.12 via Miniconda)

#### 1. Clona il repository

```bash
git clone https://github.com/AlbGri/controller-click-trainer.git
cd controller-click-trainer
```

#### 2. Crea environment conda

```bash
conda create -n click-trainer python=3.12 -y
conda activate click-trainer
```

#### 3. Installa dipendenze

```bash
pip install -r requirements.txt
```

#### 4. Avvia

```bash
python src/main.py
```

## Uso Rapido

1. Collega il controller al PC
2. Avvia l'applicazione
3. Imposta la soglia target in ms (default: 50ms)
4. Seleziona il pulsante da monitorare (o "Tutti")
5. Premi **Avvia** e inizia a premere
6. Ogni pressione appare come barra nel grafico: verde = sotto soglia (bene), rosso = sopra (troppo lungo)
7. Il numero grande mostra la durata dell'ultima pressione
8. Premi **Ferma** poi **Salva sessione**

## Struttura Progetto

```
controller-click-trainer/
├── src/
│   ├── main.py               # Entry point (supporta exe PyInstaller)
│   ├── controller_monitor.py  # Rilevamento controller, traccia press/release
│   ├── data_manager.py        # Gestione dati, profili, CSV
│   ├── diagnostics.py         # Diagnostica: polling rate, latenza, jitter
│   ├── visualizer.py          # Grafici matplotlib (barre real-time + storici)
│   └── gui.py                 # Interfaccia grafica tkinter
├── config/
│   └── settings.json          # Configurazione applicazione
├── data/                      # Sessioni salvate (CSV)
├── docs/
│   ├── usage_guide.md         # Guida uso dettagliata
│   └── github_workflow.md     # Guida pubblicazione GitHub + build exe
├── ControllerClickTrainer.spec  # Config PyInstaller per build exe
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Troubleshooting

### Controller non rilevato
- Verifica che il controller sia acceso e connesso
- Se usi DS4Windows, assicurati che l'emulazione Xbox sia attiva
- Prova a scollegare e ricollegare il controller

### Pressione non registrata
- La pressione viene registrata solo al **rilascio** del tasto (serve press + release)
- Se premi troppo velocemente, potrebbe sembrare che non registri: guarda il log in basso a destra

### Errore import moduli
- Verifica di aver attivato l'environment: `conda activate click-trainer`
- Reinstalla le dipendenze: `pip install -r requirements.txt`

## Dipendenze

| Libreria | Uso |
|---|---|
| matplotlib | Grafici barre real-time e storici |
| numpy | Calcoli numerici |
| inputs | Lettura input controller (press/release) |
| tkinter | Interfaccia grafica (incluso in Python) |

## Build Exe (per sviluppatori)

Per creare l'exe standalone:

```bash
conda activate click-trainer
pip install pyinstaller
pyinstaller ControllerClickTrainer.spec --noconfirm
```

L'exe sara' in `dist\ControllerClickTrainer\ControllerClickTrainer.exe`.

Per istruzioni dettagliate su build, release GitHub e workflow completo, vedi [docs/github_workflow.md](docs/github_workflow.md).

## Licenza

MIT License - vedi [LICENSE](LICENSE)
