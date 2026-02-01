# Guida Uso - Controller Click Trainer

## Concetto Base

Questo tool misura **quanto tempo tieni premuto un tasto** del controller, non quante volte lo premi al secondo.

Ogni pressione viene registrata quando **rilasci** il tasto: il tool misura il tempo tra il press e il release in millisecondi. L'obiettivo e' fare pressioni il piu' brevi possibile, stando **sotto** una soglia target.

## Primo Avvio

```
conda activate click-trainer
cd c:\Alberto\Coding\controller-click-trainer
python src/main.py
```

## Interfaccia

- **In alto a sinistra**: durata ultima pressione (grande, colorata) + statistiche (min, media, max, totale, sotto soglia)
- **In alto a destra**: configurazione (profilo, soglia in ms, pulsante, azioni)
- **Al centro**: grafico a barre dove ogni barra = 1 pressione. Altezza = durata in ms
- **In basso a sinistra**: diagnostica connessione (polling rate, latenza, jitter)
- **In basso a destra**: log scrollabile di ogni pressione con pulsante e durata

## Sessione di Allenamento

### 1. Configura

- **Soglia durata (ms)**: il tuo obiettivo. Es. 50ms significa che vuoi pressioni sotto 50ms. Premi "Applica" dopo aver cambiato
- **Pulsante**: scegli quale monitorare. "Tutti" li conta tutti
- **Profilo**: seleziona o crea con "+"

### 2. Avvia e premi

- Premi "Avvia"
- Premi il tasto del controller il piu' velocemente possibile
- Ogni volta che **rilasci** il tasto, appare una barra nel grafico
- **Verde** = durata sotto soglia (bene, tap veloce)
- **Rosso** = durata sopra soglia (troppo lento/lungo)

### 3. Leggi i risultati

- **Durata minima**: il tuo tap piu' breve nella sessione. Questo e' il tuo limite fisico
- **Durata media**: la tua velocita tipica
- **Sotto soglia**: quante pressioni su quante totali erano sotto il target
- **Log**: ogni riga mostra pulsante e durata esatta

### 4. Salva

Premi "Ferma" poi "Salva sessione". I dati finiscono nel CSV del profilo.

## Interpretare i Risultati

### Durata minima bassa ma media alta
Sai fare tap brevi ma non sei costante. Allenati sulla consistenza.

### Durata minima alta (es. > 30ms) nonostante tap velocissimi
Il controller potrebbe avere una risoluzione limitata o aggiungere latenza. Confronta USB vs Bluetooth nei grafici storici.

### Polling rate basso (< 100 Hz)
Il controller aggiorna la posizione meno frequentemente. Con 125 Hz (USB tipico), la risoluzione minima e' circa 8ms. Con Bluetooth puo' essere peggio.

## Grafici Storici

- **Progressi**: durata min e media sessione per sessione (asse Y invertito: piu' basso = meglio)
- **Distribuzione**: istogramma delle durate medie
- **Diagnostica**: latenza e jitter per sessione
- **Report**: riepilogo testuale con confronto USB vs Bluetooth

## File CSV

Ogni riga contiene:
```
timestamp, username, button, press_count, session_duration_s,
min_duration_ms, avg_duration_ms, max_duration_ms,
connection_type, latency_avg_ms, jitter_ms,
threshold_ms, threshold_successes
```

## Configurazione (settings.json)

| Parametro | Descrizione | Default |
|---|---|---|
| soglia_durata_ms_default | Soglia iniziale in ms | 50.0 |
| intervallo_aggiornamento_ms | Frequenza refresh UI | 50 |
| profilo_default | Profilo iniziale | "default" |
| colori | Tema colori interfaccia | (vedi file) |
