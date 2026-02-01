# Guida Workflow GitHub

Procedura completa per pubblicare un progetto Python su GitHub con release exe.

---

## Parte 1: Setup Iniziale Account GitHub (una tantum)

### 1.1 Configurare Email Noreply

GitHub nasconde la tua email privata per prevenire spam. Per evitare errori di push:

1. Vai su https://github.com/settings/emails
2. Spunta **"Keep my email addresses private"**
3. Spunta **"Block command line pushes that expose my email"**
4. Copia l'indirizzo noreply mostrato: `TUO-USERNAME@users.noreply.github.com`

Questo e' il tuo indirizzo da usare nei commit.

### 1.2 Configurare Git Globalmente (opzionale)

Per applicare queste impostazioni a **tutti** i tuoi progetti:

```bash
git config --global user.name "TUO-USERNAME"
git config --global user.email "TUO-USERNAME@users.noreply.github.com"
```

**NOTA**: Se usi l'email noreply globale, non avrai piu' l'errore `GH007` nei push.

---

## Parte 2: Pubblicare un Progetto Nuovo

### 2.1 Preparare il Progetto Localmente

Assicurati di avere:
- File `.gitignore` configurato (esclude `__pycache__`, `dist/`, `build/`, file dati sensibili)
- `README.md` e documentazione aggiornati
- `LICENSE` (se applicabile)

### 2.2 Inizializzare il Repository Git

```bash
cd /path/to/progetto
git init
```

### 2.3 Configurare Git per Questo Progetto (se non fatto globalmente)

```bash
git config user.name "AlbGri"
git config user.email "AlbGri@users.noreply.github.com"
```

Questo vale solo per il progetto corrente.

### 2.4 Primo Commit

```bash
git add -A
git status  # Verifica i file aggiunti
git commit -m "Initial commit: descrizione progetto

Breve descrizione delle funzionalita principali.
Opzionale: lista dipendenze o tecnologie usate."
```

**NOTA**: Se vuoi rimuovere tracce di AI dal commit, evita righe come `Co-Authored-By: Claude`.

### 2.5 Creare Repository su GitHub

1. Vai su https://github.com/new
2. **Repository name**: nome-progetto (kebab-case)
3. **Description**: breve descrizione (max 1 riga)
4. Scegli **Public** o **Private**
5. **NON** spuntare "Add a README" (gia' presente in locale)
6. **NON** spuntare "Add .gitignore" (gia' presente in locale)
7. **NON** scegliere una License (gia' presente se applicabile)
8. Clicca **Create repository**

### 2.6 Collegare Repository Locale a GitHub

Dopo aver creato il repo, GitHub mostra i comandi. Usa questi:

```bash
git remote add origin https://github.com/TUO-USERNAME/nome-progetto.git
git branch -M main
git push -u origin main
```

### 2.7 Gestire Errore Email Privacy (se si verifica)

Se ricevi questo errore:

```
error: GH007: Your push would publish a private email address.
You can make your email public or disable this protection by visiting:
https://github.com/settings/emails
```

**Soluzione**:

1. Configura l'email noreply (vedi 1.1)
2. Correggi il commit:

```bash
git config user.email "TUO-USERNAME@users.noreply.github.com"
git commit --amend --reset-author --no-edit
git push -u origin main
```

Se il remote URL usa minuscole ma il tuo username ha maiuscole, aggiornalo:

```bash
git remote set-url origin https://github.com/TuoUsername/nome-progetto.git
```

---

## Parte 3: Build Exe con PyInstaller (Progetti Python)

### 3.1 Installare PyInstaller

Attiva l'environment conda del progetto:

```bash
conda activate nome-env
pip install pyinstaller
```

### 3.2 Creare File .spec

Crea un file `NomeProgetto.spec` nella root del progetto:

```python
# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# DLL conda mancanti (se usi tkinter, matplotlib, etc.)
CONDA_BIN = os.path.join(
    os.environ.get('CONDA_PREFIX', r'C:\Users\USERNAME\.conda\envs\ENV-NAME'),
    'Library', 'bin'
)

a = Analysis(
    ['src/main.py'],  # Entry point
    pathex=[],
    binaries=[
        # DLL conda che PyInstaller non trova automaticamente
        (os.path.join(CONDA_BIN, 'tcl86t.dll'), '.'),
        (os.path.join(CONDA_BIN, 'tk86t.dll'), '.'),
        (os.path.join(CONDA_BIN, 'ffi.dll'), '.'),
        (os.path.join(CONDA_BIN, 'liblzma.dll'), '.'),
        (os.path.join(CONDA_BIN, 'libbz2.dll'), '.'),
        (os.path.join(CONDA_BIN, 'libexpat.dll'), '.'),
    ],
    datas=[
        ('config/settings.json', 'config'),  # File config
    ],
    hiddenimports=[
        'src',
        'src.modulo1',
        'src.modulo2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NomeProgetto',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False = solo GUI, True = mostra console
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NomeProgetto',
)
```

### 3.3 Modificare main.py per Supportare Exe

Aggiungi all'inizio di `src/main.py`:

```python
import os
import sys
from pathlib import Path

# Rileva se in esecuzione come exe PyInstaller
if getattr(sys, 'frozen', False):
    # Exe PyInstaller: la directory base e' dove si trova l'exe
    BASE_DIR = Path(sys.executable).resolve().parent
    # Imposta working directory alla cartella dell'exe
    os.chdir(BASE_DIR)
    PROJECT_ROOT = BASE_DIR
else:
    # Esecuzione normale da sorgente
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

Questo permette all'exe di trovare file config e cartelle dati con percorsi relativi.

### 3.4 Buildare l'Exe

```bash
pyinstaller NomeProgetto.spec --noconfirm
```

L'exe sara' in `dist/NomeProgetto/NomeProgetto.exe`.

### 3.5 Copiare File Config Accanto all'Exe

PyInstaller mette i dati in `_internal/`, ma l'app cerca percorsi relativi alla cartella exe:

```bash
# PowerShell
Copy-Item -Path "dist\NomeProgetto\_internal\config" -Destination "dist\NomeProgetto\config" -Recurse
```

Ora l'utente puo' modificare `config/settings.json` accanto all'exe.

### 3.6 Creare ZIP per Distribuzione

```bash
# PowerShell
Compress-Archive -Path "dist\NomeProgetto\*" -DestinationPath "NomeProgetto-v1.0.0-windows.zip" -Force
```

---

## Parte 4: Creare Release su GitHub

### 4.1 Installare GitHub CLI

**Via winget** (consigliato):

```bash
winget install --id GitHub.cli
```

Riavvia il terminale dopo l'installazione (o usa il percorso completo: `C:\Program Files\GitHub CLI\gh.exe`).

### 4.2 Autenticare GitHub CLI

**Prima volta**:

```bash
gh auth login
```

Segui le istruzioni:
1. Scegli **GitHub.com**
2. Scegli **HTTPS**
3. Autentica via **browser** (apre automaticamente) o **token** (da https://github.com/settings/tokens)

Verifica autenticazione:

```bash
gh auth status
```

### 4.3 Creare Release con ZIP

```bash
gh release create v1.0.0 NomeProgetto-v1.0.0-windows.zip \
  --title "v1.0.0 - Prima release" \
  --notes "Descrizione delle funzionalita principali.

**Istruzioni installazione**:
1. Scarica il file ZIP
2. Estrai in una cartella
3. Esegui `NomeProgetto.exe`

**Requisiti**: Windows 10/11 (nessuna dipendenza Python richiesta)"
```

**Opzioni utili**:
- `--draft`: crea release bozza (non visibile pubblicamente)
- `--prerelease`: marca come versione pre-release (beta, alpha)
- `--latest`: marca come latest release (default per prima release)

### 4.4 Aggiornare Release Esistente

Per aggiungere file a una release gia' creata:

```bash
gh release upload v1.0.0 file-aggiuntivo.zip
```

Per modificare note:

```bash
gh release edit v1.0.0 --notes "Nuove note"
```

---

## Parte 5: Workflow Aggiornamenti Futuri

### 5.1 Modificare Codice e Committare

```bash
git add -A
git status
git commit -m "Fix bug nella funzione X"
git push
```

### 5.2 Creare Nuova Release (es. v1.1.0)

1. Aggiorna versione in `src/__init__.py`:
   ```python
   __version__ = "1.1.0"
   ```

2. Rebuild exe:
   ```bash
   pyinstaller NomeProgetto.spec --noconfirm
   Copy-Item -Path "dist\NomeProgetto\_internal\config" -Destination "dist\NomeProgetto\config" -Recurse
   Compress-Archive -Path "dist\NomeProgetto\*" -DestinationPath "NomeProgetto-v1.1.0-windows.zip" -Force
   ```

3. Commit e tag:
   ```bash
   git add -A
   git commit -m "Release v1.1.0: descrizione cambiamenti"
   git tag v1.1.0
   git push && git push --tags
   ```

4. Crea release:
   ```bash
   gh release create v1.1.0 NomeProgetto-v1.1.0-windows.zip \
     --title "v1.1.0 - Descrizione breve" \
     --notes "**Novita'**:
   - Feature 1
   - Bugfix 2

   **Breaking changes**: nessuno"
   ```

---

## Parte 6: Comandi Utili GitHub CLI

### Repository

```bash
gh repo view                    # Visualizza repo corrente
gh repo view --web              # Apre repo nel browser
gh repo clone OWNER/REPO        # Clona un repo
```

### Issues

```bash
gh issue list                   # Lista issue
gh issue create --title "Titolo" --body "Descrizione"
gh issue close NUMERO
```

### Pull Requests

```bash
gh pr list                      # Lista PR
gh pr create --title "Titolo" --body "Descrizione"
gh pr merge NUMERO
```

### Releases

```bash
gh release list                 # Lista release
gh release view v1.0.0          # Dettagli release
gh release delete v1.0.0        # Elimina release
gh release download v1.0.0      # Scarica asset release
```

---

## Parte 7: Risoluzione Problemi Comuni

### Errore: "remote: Repository not found"

**Causa**: URL remote errato o repo privato senza accesso.

**Soluzione**:

```bash
git remote -v  # Verifica URL
git remote set-url origin https://github.com/USERNAME/REPO.git
```

### Errore: "Updates were rejected because the tip of your current branch is behind"

**Causa**: Qualcuno ha pushato mentre lavoravi.

**Soluzione**:

```bash
git pull --rebase  # Scarica modifiche remote e riapplica le tue sopra
git push
```

### Errore: "gh: command not found" dopo installazione

**Causa**: PATH non aggiornato.

**Soluzione**:

- **Windows**: riavvia terminale o usa percorso completo `C:\Program Files\GitHub CLI\gh.exe`
- Oppure aggiungi manualmente al PATH: `setx PATH "%PATH%;C:\Program Files\GitHub CLI"`

### Exe non trova file config o DLL mancanti

**Causa**: File non inclusi nel build PyInstaller.

**Soluzione**:

1. **Config**: aggiungi in `datas` nel .spec
2. **DLL conda**: aggiungi in `binaries` nel .spec (percorso `Library\bin`)
3. Rebuild: `pyinstaller NomeProgetto.spec --noconfirm`

### Exe mostra errori ma da sorgente funziona

**Causa**: PyInstaller non trova import nascosti.

**Soluzione**:

Aggiungi in `hiddenimports` nel .spec:

```python
hiddenimports=[
    'modulo_problematico',
    'modulo_problematico.submodulo',
],
```

---

## Parte 8: Best Practices

### Commit Messages

- **Formato**: `Tipo: breve descrizione` (max 50 caratteri)
- **Tipi**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- **Esempi**:
  - `feat: aggiungi modalita scura`
  - `fix: correggi crash al salvataggio`
  - `docs: aggiorna README con istruzioni installazione`

### Versionamento (Semantic Versioning)

Formato: `MAJOR.MINOR.PATCH` (es. `1.2.3`)

- **MAJOR**: cambiamenti incompatibili (breaking changes)
- **MINOR**: nuove funzionalita retrocompatibili
- **PATCH**: bugfix retrocompatibili

**Esempi**:
- `1.0.0` → `1.0.1`: bugfix
- `1.0.1` → `1.1.0`: nuova feature
- `1.1.0` → `2.0.0`: breaking change (API cambiata, richiede modifiche codice utente)

### .gitignore

Includi sempre:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.spec  # Opzionale: se vuoi versionare il .spec, rimuovi questa riga

# Dati generati
data/*.csv
data/*.json  # Se contengono dati utente

# Environment
.env
.venv/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### File da Non Committare Mai

- **Credenziali**: `.env`, `secrets.json`, token API
- **Dati utente**: file CSV con dati personali, database locali
- **File grandi** (> 50 MB): usa Git LFS o host esterno (Google Drive, release asset)

---

## Riepilogo Comandi Quick Reference

### Setup Iniziale (una tantum)

```bash
git config --global user.name "Username"
git config --global user.email "username@users.noreply.github.com"
winget install --id GitHub.cli
gh auth login
```

### Nuovo Progetto

```bash
cd progetto
git init
git add -A
git commit -m "Initial commit"
# Crea repo su GitHub (web)
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

### Build e Release

```bash
# Build exe
pyinstaller Progetto.spec --noconfirm
Copy-Item -Path "dist\Progetto\_internal\config" -Destination "dist\Progetto\config" -Recurse

# Crea ZIP
Compress-Archive -Path "dist\Progetto\*" -DestinationPath "Progetto-v1.0.0-windows.zip" -Force

# Release
gh release create v1.0.0 Progetto-v1.0.0-windows.zip \
  --title "v1.0.0" --notes "Prima release"
```

### Aggiornamento Codice

```bash
git add -A
git commit -m "Descrizione modifiche"
git push
```

---

**Fine Guida** | Per domande: https://docs.github.com/cli | PyInstaller: https://pyinstaller.org/en/stable/
