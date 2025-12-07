# Comic Viewer - App Visualizzatore Vignette

App Kivy per Android che permette di visualizzare vignette/fumetti giornalieri da GitHub.

## Repository Immagini

Le immagini vengono caricate da:
`https://github.com/sagara939/Visualizzatore_vignette`

## Funzionalità

- **Swipe orizzontale**: passa alla vignetta precedente/successiva
- **Zoom con due dita**: ingrandisce l'immagine (pinch-to-zoom)
- **Scroll verticale**: per vignette lunghe
- **Menu serie**: seleziona tra diverse serie di fumetti
- **Config remota**: aggiorna automaticamente le serie disponibili dal repository GitHub

## Struttura File

```
Visualizzatore_vignette/
├── run_v1.0.py        # App principale
├── requirements.txt    # Dipendenze Python
├── buildozer.spec     # Config per compilazione Android
├── config.json        # Config locale serie
├── cache/             # Cache immagini (creata automaticamente)
├── comics/            # Cartella immagini (su GitHub)
│   ├── serie1/        # Prima serie
│   │   ├── 2025-12-01.png
│   │   ├── 2025-12-02.png
│   │   └── ...
│   └── serie2/        # Seconda serie
│       ├── 2025-12-01.png
│       └── ...
└── README.md          # Questo file
```

## Installazione (Sviluppo)

```bash
# Crea ambiente virtuale
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install kivy[base] requests Pillow

# Esegui l'app
python run_v1.0.py
```

## Compilazione APK Android

### Prerequisiti (Linux/WSL necessario)
- Python 3.8+
- Java JDK 11
- Android SDK
- Android NDK

### Comandi

```bash
# Installa buildozer
pip install buildozer

# Compila APK debug
buildozer android debug

# Compila APK release
buildozer android release
```

L'APK sarà generato in `bin/comicviewer-1.0.0-debug.apk`

## Struttura GitHub per le Immagini

Nel repository GitHub, crea le cartelle:

```
comics/
├── serie1/
│   ├── 2025-12-01.png
│   ├── 2025-12-02.png
│   └── ...
└── serie2/
    ├── 2025-12-01.png
    └── ...
```

Le immagini vengono caricate come:
`https://raw.githubusercontent.com/sagara939/Visualizzatore_vignette/main/comics/{serie}/{data}.png`

## Aggiungere Nuove Serie

1. Crea una nuova cartella in `comics/` nel repository GitHub
2. Aggiungi la serie nel file `config.json`:

```json
{
  "name": "Nuova Serie",
  "base_url": "https://raw.githubusercontent.com/sagara939/Visualizzatore_vignette/main/comics/nuovaserie/",
  "date_format": "%Y-%m-%d",
  "file_extension": ".png",
  "description": "Descrizione serie"
}
```

3. Pusha le modifiche su GitHub
4. Nell'app, premi ⟳ per aggiornare le serie

## Formato Data

Formati supportati per `date_format`:
- `%Y-%m-%d` → 2025-12-07
- `%Y%m%d` → 20251207
- `%d-%m-%Y` → 07-12-2025

## Note

- L'app richiede connessione internet per caricare le vignette da GitHub
- La configurazione viene salvata localmente come fallback
- Premi il pulsante ⟳ per aggiornare le serie dal repository
