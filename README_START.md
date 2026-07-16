# Local Start Instructions
Run the newly refactored backend locally by typing:

   1. Klon vectorbt (brak w repo, vendored):

   1 git clone https://github.com/polakowo/vectorbt.git vectorbt_src

   2. Python venv i pakiety (uv auto-tworzy .venv):

   1 uv sync --extra dev

   3. Frontend pakiety:
   1 cd frontend && npm install && cd ..

   4. Uruchom testy:
   1 make test

   5. Start (FastAPI + Vite):
  Opcja A (prostsza): uruchom ./run_local.sh. Skrypt auto-generuje plik .env i odpala backend + frontend w tle.
  Opcja B (Make): make dev (wymaga dwóch terminali) lub osobno make api i cd frontend && npm run dev.
