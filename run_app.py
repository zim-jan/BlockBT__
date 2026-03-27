import subprocess
import sys
from pathlib import Path

# Make sure the source package is importable regardless of working directory.
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT / "src"))

from blockbt.db.session import init_db  # noqa: E402, I001

def main():
    # ── One-time DB initialisation (creates tables if they don't exist) ───────────
    init_db()

    # ── Run Streamlit app ─────────────────────────────────────────────────────────
    # Uruchomienie streamlit w podprocesie pozwala na poprawne odizolowanie środowiska.
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    main()
