#!/usr/bin/env bash

# Skrypt uruchamiający środowisko lokalne BlockBT bez Dockera

set -e

# Kolory w konsoli
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Inicjalizacja BlockBT (Local) ===${NC}"

# 1. Sprawdzenie .env i wygenerowanie SECRET_KEY jeśli brakuje
#    SECRET_KEY musi być kluczem Fernet (URL-safe base64, 32 bajty) — `openssl base64`
#    daje zwykły base64 i Fernet go odrzuca, dlatego generujemy przez cryptography.
gen_secret_key() {
    uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

if [ ! -f .env ]; then
    echo -e "${YELLOW}Brak pliku .env. Tworzę na podstawie .env.example...${NC}"
    cp .env.example .env
    SECRET_KEY=$(gen_secret_key)
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    echo -e "${GREEN}Plik .env został wygenerowany z nowym SECRET_KEY.${NC}"
elif ! grep -qE "^SECRET_KEY=.+" .env; then
    echo -e "${YELLOW}Brak SECRET_KEY w .env. Generuję i dopisuję...${NC}"
    echo "SECRET_KEY=$(gen_secret_key)" >> .env
    echo -e "${GREEN}Dopisano SECRET_KEY do .env.${NC}"
else
    echo -e "${GREEN}Plik .env z SECRET_KEY już istnieje.${NC}"
fi

# 2. Utworzenie niezbędnych folderów (ścieżki zgodne z DATA_DIR w backend/app/core/config.py)
echo -e "${BLUE}Sprawdzanie katalogów lokalnych...${NC}"
mkdir -p backend/data/cache
mkdir -p backend/data/logs

# 3. Instalacja frontendu jeśli brakuje node_modules
echo -e "${BLUE}Sprawdzanie pakietów frontendu...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Katalog node_modules nie istnieje, instaluję zależności frontendu...${NC}"
    (cd frontend && npm install)
    echo -e "${GREEN}Zależności frontendu zainstalowane.${NC}"
fi

# Zmienne do przechowania PID procesów
BACKEND_PID=""
FRONTEND_PID=""

# Funkcja sprzątająca (cleanup)
cleanup() {
    echo -e "\n${YELLOW}Otrzymano sygnał zatrzymania. Zamykam aplikację...${NC}"
    if [ -n "$FRONTEND_PID" ]; then
        echo "Zatrzymywanie frontendu (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ -n "$BACKEND_PID" ]; then
        echo "Zatrzymywanie backendu (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Zatrzymano wszystkie procesy. Do widzenia!${NC}"
    exit 0
}

# Nasłuchiwanie na sygnały (Ctrl+C, etc)
trap cleanup SIGINT SIGTERM EXIT

# 4. Uruchomienie Backendu (w tle)
echo -e "${BLUE}Uruchamianie backendu (FastAPI)...${NC}"
# Pakiet `app` mieszka w backend/ (patrz [tool.setuptools.packages.find] w pyproject.toml),
# więc uvicorn musi startować z tego katalogu.
(cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!
echo -e "${GREEN}Backend uruchomiony (PID: $BACKEND_PID) na porcie 8000.${NC}"

# Poczekajmy chwilkę, żeby uvicorn zaczął logować
sleep 2

# 5. Uruchomienie Frontendu
echo -e "${BLUE}Uruchamianie frontendu (React / Vite)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}Frontend uruchomiony (PID: $FRONTEND_PID) na porcie 3000.${NC}"

echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}BlockBT uruchomiony lokalnie!${NC}"
echo -e "${GREEN}Backend API: http://127.0.0.1:8000/docs${NC}"
echo -e "${GREEN}Frontend:    http://127.0.0.1:3000${NC}"
echo -e "${YELLOW}Naciśnij Ctrl+C aby wyłączyć wszystko.${NC}"
echo -e "${GREEN}===========================================${NC}\n"

# Oczekiwanie w nieskończoność aż użytkownik zrobi Ctrl+C
wait
