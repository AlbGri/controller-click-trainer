"""Entry point dell'applicazione Controller Click Trainer.

Configura logging, verifica dipendenze e avvia la GUI.
"""

import logging
import os
import sys
from pathlib import Path

# Rileva se in esecuzione come exe PyInstaller
if getattr(sys, 'frozen', False):
    # Exe PyInstaller: la directory base e' dove si trova l'exe
    BASE_DIR = Path(sys.executable).resolve().parent
    # Imposta la working directory alla cartella dell'exe
    # cosi i percorsi relativi (data/, config/) funzionano
    os.chdir(BASE_DIR)
    PROJECT_ROOT = BASE_DIR
else:
    # Esecuzione normale da sorgente
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def setup_logging() -> None:
    """Configura il sistema di logging."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def check_dependencies() -> bool:
    """Verifica che tutte le dipendenze siano disponibili.

    Returns:
        True se tutte le dipendenze sono presenti
    """
    missing = []

    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    try:
        import inputs
    except ImportError:
        missing.append("inputs")

    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")

    if missing:
        print(f"ERRORE: Dipendenze mancanti: {', '.join(missing)}")
        print("Installa con: pip install -r requirements.txt")
        return False

    return True


def main() -> None:
    """Funzione principale: configura e avvia l'applicazione."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Avvio Controller Click Trainer")

    if not check_dependencies():
        sys.exit(1)

    # Import dopo verifica dipendenze
    from src.gui import App

    try:
        app = App()
        app.run()
    except KeyboardInterrupt:
        logger.info("Applicazione interrotta dall'utente")
    except Exception as e:
        logger.exception("Errore fatale: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
