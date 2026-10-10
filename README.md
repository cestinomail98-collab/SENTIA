# SENTIA — organismo dati

Un **monitor di sistema vivente** per Windows: non una dashboard, un organismo.
Il tuo PC ha un cuore che respira, un battito cardiaco legato alla CPU, satelliti
in orbita (CPU · RAM · DISCO · RETE · BATTERIA · GPU · PING) e persino uno stato
emotivo che riflette lo stress del sistema.

## Cosa fa

- **Dati reali ogni 2 secondi** via ponte Python + psutil: CPU (per-core), RAM,
  disco (uso + I/O), rete (throughput, ping, jitter, perdita pacchetti),
  batteria, processi dominanti, GPU e temperature quando i driver le espongono
- **Vista ORGANISMO**: flow-field di particelle reattive al mouse, cuore
  generativo afferrabile, satelliti orbitali con fili elastici, cursore
  magnetico, pannelli di vetro trascinabili con inerzia
- **Vista ANALISI**: griglia dei core in tempo reale, top processi per CPU/RAM,
  storico della rete, info di sistema — con transizione a onda d'urto + whoosh
- **Audio**: soundscape generativo WebAudio (drone che segue la salute, note
  pentatoniche suonate dai satelliti, thump sub sul battito) + SFX reali
- **Modalità CAOS** manuale o automatica (scatta oltre il 95% di CPU)
- **SINGOLARITÀ**: l'intero sistema collassa e rinasce
- **Fallback browser**: senza il ponte usa i sensori del browser (FPS, heap,
  batteria, rete)

## Avvio

- **SENTIA.exe** (build PyInstaller in `dist/`): doppio click, fa tutto da solo
- oppure `SENTIA.vbs` / `AVVIA-SENTIA.bat`
- oppure manualmente: `python server.py` → http://localhost:7107/
- `Crea-icona-desktop.bat` crea il collegamento sul Desktop con l'icona dedicata

## Build dell'eseguibile

```
pip install pyinstaller psutil
pyinstaller --onefile --noconsole --name SENTIA --icon sentia.ico \
  --add-data "sentia.html;." --add-data "sentia.ico;." \
  --add-data "wallpaper.jpg;." --add-data "sfx-whoosh.mp3;." --add-data "sfx-boom.mp3;." \
  server.py
```

## Tech

Vanilla HTML/CSS/JS (canvas 2D, WebAudio API, SVG) + Python stdlib
(`http.server`) + `psutil`. Nessun framework, nessuna build pipeline.
