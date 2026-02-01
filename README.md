# Controller Click Trainer

Applicazione desktop per monitorare e allenare la **durata delle pressioni** sui controller gaming (Xbox, DS4Windows).
Misura in millisecondi quanto tempo un tasto resta premuto, fornisce feedback visivo rispetto a una soglia configurabile e salva le statistiche per tracciare i progressi.

## A cosa serve

In giochi come Rocket League, la durata della pressione di un tasto influenza direttamente il gameplay: tenere premuto il salto piu' a lungo significa saltare piu' in alto. Questo tool ti aiuta a:

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
- Python 3.8+ (consigliato 3.12 via Miniconda)
- Controller Xbox o compatibile (anche DS4Windows con emulazione Xbox)

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/tuo-username/controller-click-trainer.git
cd controller-click-trainer
```

### 2. Crea environment conda (consigliato)

```bash
conda create -n click-trainer python=3.12 -y
conda activate click-trainer
```

### 3. Installa dipendenze

```bash
pip install -r requirements.txt
```

### 4. Avvia

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
│   ├── main.py               # Entry point
│   ├── controller_monitor.py  # Rilevamento controller, traccia press/release
│   ├── data_manager.py        # Gestione dati, profili, CSV
│   ├── diagnostics.py         # Diagnostica: polling rate, latenza, jitter
│   ├── visualizer.py          # Grafici matplotlib (barre real-time + storici)
│   └── gui.py                 # Interfaccia grafica tkinter
├── config/
│   └── settings.json          # Configurazione applicazione
├── data/                      # Sessioni salvate (CSV)
├── docs/
│   └── usage_guide.md         # Guida uso dettagliata
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

## Licenza

MIT License - vedi [LICENSE](LICENSE)
