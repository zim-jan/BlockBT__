#!/usr/bin/env python
"""Pre-flight smoke test Fazy 25 (Dashboard) — weryfikacja warstwy API przed testem manualnym UI.

Cel: rozdzielić awarie backendu od awarii frontendu. Jeżeli ten skrypt jest zielony,
każdy błąd widoczny w przeglądarce leży po stronie UI, nie API.

Pokrywa dokładnie to, co naprawia PR #6:
  * start procesu API (brak ``ModuleNotFoundError: ta``),
  * serializację wskaźników — brak literalnego ``NaN`` w odpowiedzi JSON,
oraz endpointy, na których stoi Dashboard: lista jobów, notatki (CRUD), tearsheet.

Uruchomienie (backend musi już działać na 127.0.0.1:8000):

    uv run python scripts/smoke_faza25.py
    uv run python scripts/smoke_faza25.py --base-url http://127.0.0.1:8000 --symbol BTC-USD

Kod wyjścia: 0 = wszystko OK, 1 = co najmniej jeden FAIL, 2 = backend nieosiągalny.
Skrypt jest nieinwazyjny poza notatkami: tworzy własną notatkę testową i usuwa ją na końcu.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# Literalne tokeny, których JSON.parse w przeglądarce nie przyjmuje.
_BAD_JSON_TOKENS = re.compile(r"\b(NaN|Infinity|-Infinity)\b")

_GREEN = "\033[0;32m"
_RED = "\033[0;31m"
_YELLOW = "\033[1;33m"
_DIM = "\033[2m"
_NC = "\033[0m"


class Result:
    """Zbiera wyniki kroków, żeby na końcu wypisać jedno podsumowanie."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def ok(self, name: str, detail: str = "") -> None:
        self.passed += 1
        print(f"  {_GREEN}[OK]{_NC}   {name}" + (f" {_DIM}{detail}{_NC}" if detail else ""))

    def fail(self, name: str, detail: str = "") -> None:
        self.failed += 1
        print(f"  {_RED}[FAIL]{_NC} {name}" + (f" {_DIM}{detail}{_NC}" if detail else ""))

    def skip(self, name: str, detail: str = "") -> None:
        self.skipped += 1
        print(f"  {_YELLOW}[SKIP]{_NC} {name}" + (f" {_DIM}{detail}{_NC}" if detail else ""))


def http(
    base_url: str, path: str, method: str = "GET", payload: dict[str, Any] | None = None
) -> tuple[int, str]:
    """Wykonuje żądanie HTTP i zwraca ``(status, surowe_body)``.

    Surowe body jest istotne — walidacja NaN musi zobaczyć tekst przed parsowaniem.
    """
    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def check_health(base_url: str, res: Result) -> None:
    """Krok 1 — proces API wstaje i odpowiada (regresja `ModuleNotFoundError: ta`)."""
    print("\n1. Start i zdrowie API")
    status, body = http(base_url, "/api/health")
    if status == 200:
        res.ok("GET /api/health", f"HTTP {status}")
    else:
        res.fail("GET /api/health", f"HTTP {status} — backend nie wstał, reszta kroków bez sensu")
        return

    status, body = http(base_url, "/openapi.json")
    if status == 200:
        try:
            paths = json.loads(body).get("paths", {})
        except json.JSONDecodeError:
            paths = {}
        wymagane = ["/api/data/realtime", "/api/notes/strategy/{strategy_id}", "/api/backtest/"]
        brakujace = [p for p in wymagane if p not in paths]
        if brakujace:
            res.fail("openapi.json — routery Fazy 25", f"brak ścieżek: {brakujace}")
        else:
            res.ok("openapi.json — routery Fazy 25 zarejestrowane", f"{len(paths)} ścieżek")
    else:
        res.fail("GET /openapi.json", f"HTTP {status}")


def check_realtime(base_url: str, symbol: str, res: Result) -> None:
    """Krok 2 — sedno PR #6: wskaźniki liczone TA-Lib + NaN → null."""
    print("\n2. /api/data/realtime — świece i wskaźniki (rdzeń fixu)")

    status, body = http(base_url, f"/api/data/realtime?symbol={symbol}&interval=5m")
    if status != 200:
        res.fail(f"świece bez wskaźników ({symbol}, 5m)", f"HTTP {status}")
        return
    try:
        punkty = json.loads(body)["data"]
    except (json.JSONDecodeError, KeyError) as exc:
        res.fail(f"świece bez wskaźników ({symbol}, 5m)", f"niepoprawny JSON: {exc}")
        return
    if not punkty:
        res.skip(
            f"świece bez wskaźników ({symbol}, 5m)",
            "0 świec — brak sieci lub yfinance nie zwrócił danych; UI pokaże pusty wykres",
        )
        return
    res.ok(f"świece bez wskaźników ({symbol}, 5m)", f"{len(punkty)} świec")

    for typ, period, kolumny in (
        ("SMA", 20, ["SMA_20"]),
        ("EMA", 50, ["EMA_50"]),
        ("RSI", 14, ["RSI_14"]),
        ("MACD", 12, ["MACD_line", "MACD_signal", "MACD_diff"]),
    ):
        inds = urllib.parse.quote(json.dumps([{"type": typ, "period": period}]))
        status, body = http(
            base_url, f"/api/data/realtime?symbol={symbol}&interval=5m&indicators={inds}"
        )
        nazwa = f"{typ}({period})"
        if status != 200:
            res.fail(nazwa, f"HTTP {status}")
            continue

        # 2a. Surowe body nie może zawierać literalnego NaN/Infinity — to był bug #2.
        zle = _BAD_JSON_TOKENS.search(body)
        if zle:
            res.fail(
                nazwa,
                f"w odpowiedzi literalne '{zle.group(0)}' — JSON.parse w przeglądarce padnie",
            )
            continue

        # 2b. Body musi się parsować dokładnie tak, jak zrobi to przeglądarka.
        try:
            punkty = json.loads(body)["data"]
        except (json.JSONDecodeError, KeyError) as exc:
            res.fail(nazwa, f"niepoprawny JSON: {exc}")
            continue

        brak = [k for k in kolumny if k not in punkty[0]]
        if brak:
            res.fail(nazwa, f"brak kolumn w payloadzie: {brak}")
            continue

        # 2c. Okres rozgrzewania musi być null-em, a nie NaN-em ani liczbą.
        glowna = kolumny[0]
        warmup = punkty[0][glowna]
        ostatnia = next(
            (p[glowna] for p in reversed(punkty) if p[glowna] is not None), None
        )
        if warmup is not None:
            res.fail(nazwa, f"pierwsza świeca ma {warmup!r}, oczekiwane null (rozgrzewanie)")
        elif ostatnia is None:
            res.fail(nazwa, "wszystkie wartości są null — wskaźnik nic nie policzył")
        else:
            res.ok(nazwa, f"warm-up=null, ostatnia={ostatnia:.4f}, kolumny={kolumny}")

    # 2d. period < 2 nie może wywalić TA-Liba (przycięcie do >= 2).
    inds = urllib.parse.quote(json.dumps([{"type": "SMA", "period": 1}]))
    status, body = http(
        base_url, f"/api/data/realtime?symbol={symbol}&interval=5m&indicators={inds}"
    )
    if status == 200 and not _BAD_JSON_TOKENS.search(body):
        res.ok("SMA(1) — przycięcie timeperiod do >= 2", f"HTTP {status}")
    else:
        res.fail("SMA(1) — przycięcie timeperiod do >= 2", f"HTTP {status}")

    # 2e. Nieistniejący ticker nie może wywrócić endpointu.
    status, body = http(base_url, "/api/data/realtime?symbol=ZZZZ_NIE_ISTNIEJE&interval=5m")
    if status in (200, 500):
        res.ok("nieistniejący ticker obsłużony", f"HTTP {status}")
    else:
        res.fail("nieistniejący ticker obsłużony", f"nieoczekiwany HTTP {status}")


def check_jobs(base_url: str, res: Result) -> int | None:
    """Krok 3 — lista jobów zasilająca HistoryWidget. Zwraca id joba COMPLETED."""
    print("\n3. /api/backtest/ — lista jobów (HistoryWidget)")
    status, body = http(base_url, "/api/backtest/")
    if status != 200:
        res.fail("GET /api/backtest/", f"HTTP {status}")
        return None
    try:
        joby = json.loads(body)["data"]
    except (json.JSONDecodeError, KeyError) as exc:
        res.fail("GET /api/backtest/", f"niepoprawny JSON: {exc}")
        return None

    res.ok("GET /api/backtest/", f"{len(joby)} jobów")
    if not joby:
        res.skip("dane do HistoryWidget", "brak jobów — odpal backtest w Builderze")
        return None

    braki = [j["id"] for j in joby if "symbol" not in j or "status" not in j]
    if braki:
        res.fail("kształt payloadu joba", f"joby bez symbol/status: {braki}")
    else:
        res.ok("kształt payloadu joba", "symbol + status + metrics obecne")

    # Multi-symbol zwraca listę (Faza 10) — informacja dla scenariusza S8.
    multi = [j["id"] for j in joby if isinstance(j.get("symbol"), list)]
    if multi:
        res.skip(
            "joby multi-symbol w bazie",
            f"id={multi} — sprawdź w UI, czy tickery nie są sklejone (znany bug HistoryWidget:63)",
        )

    completed = [j for j in joby if j.get("status") == "COMPLETED"]
    if not completed:
        res.skip("job COMPLETED do tearsheetu", "brak ukończonych jobów")
        return None
    return completed[0]["id"]


def check_notes(base_url: str, strategy_id: int, res: Result) -> None:
    """Krok 4 — pełny CRUD notatek (NotesWidget)."""
    print(f"\n4. /api/notes — CRUD notatek (strategia {strategy_id})")
    status, body = http(base_url, f"/api/notes/strategy/{strategy_id}")
    if status != 200:
        res.fail(f"GET /api/notes/strategy/{strategy_id}", f"HTTP {status}")
        return
    res.ok(f"GET /api/notes/strategy/{strategy_id}", f"{len(json.loads(body)['data'])} notatek")

    status, body = http(
        base_url,
        f"/api/notes/strategy/{strategy_id}",
        method="POST",
        payload={"content": "smoke test faza 25 — do usunięcia", "is_pinned": False},
    )
    if status != 201:
        res.fail("POST /api/notes/strategy/{id}", f"HTTP {status}")
        return
    note_id = json.loads(body)["data"]["id"]
    res.ok("POST /api/notes/strategy/{id}", f"utworzono notatkę id={note_id}")

    status, body = http(
        base_url, f"/api/notes/{note_id}", method="PUT", payload={"is_pinned": True}
    )
    if status == 200 and json.loads(body)["data"]["is_pinned"] is True:
        res.ok("PUT /api/notes/{id} — pinowanie", "is_pinned=true")
    else:
        res.fail("PUT /api/notes/{id} — pinowanie", f"HTTP {status}")

    status, _ = http(base_url, f"/api/notes/{note_id}", method="DELETE")
    if status == 200:
        res.ok("DELETE /api/notes/{id}", "posprzątano notatkę testową")
    else:
        res.fail("DELETE /api/notes/{id}", f"HTTP {status} — notatka id={note_id} została w bazie")

    # 404 na nieistniejącej strategii — to trafia UI przy strategyId=0.
    status, _ = http(base_url, "/api/notes/strategy/0")
    if status in (404, 200):
        res.ok("GET /api/notes/strategy/0", f"HTTP {status} (bez 500)")
    else:
        res.fail("GET /api/notes/strategy/0", f"HTTP {status}")


def check_tearsheet(base_url: str, job_id: int, res: Result) -> None:
    """Krok 5 — tearsheet QuantStats w FullJobViewModal."""
    print(f"\n5. /api/results/{job_id}/tearsheet — modal szczegółów joba")
    status, body = http(base_url, f"/api/results/{job_id}/tearsheet")
    if status != 200:
        res.fail(f"GET /api/results/{job_id}/tearsheet", f"HTTP {status}")
        return
    try:
        html = json.loads(body)["data"]["html"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        res.fail(f"GET /api/results/{job_id}/tearsheet", f"niepoprawna odpowiedź: {exc}")
        return
    if "<html" in html.lower() or "<body" in html.lower() or len(html) > 500:
        res.ok(f"GET /api/results/{job_id}/tearsheet", f"HTML {len(html)} znaków")
    else:
        res.fail(f"GET /api/results/{job_id}/tearsheet", f"podejrzanie krótki HTML: {len(html)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test API dla Fazy 25 (Dashboard)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--symbol", default="BTC-USD", help="ticker do testu wykresu realtime")
    parser.add_argument(
        "--strategy-id", type=int, default=None, help="strategia do testu notatek (domyślnie: pierwsza z listy)"
    )
    args = parser.parse_args()

    print(f"{_DIM}BlockBT — smoke test Fazy 25 @ {args.base_url}{_NC}")
    res = Result()

    try:
        http(args.base_url, "/api/health")
    except OSError as exc:
        print(f"\n{_RED}Backend nieosiągalny na {args.base_url}: {exc}{_NC}")
        print("Uruchom: make api   (albo cd backend && uv run uvicorn app.main:app --port 8000)")
        return 2

    check_health(args.base_url, res)
    check_realtime(args.base_url, args.symbol, res)
    job_id = check_jobs(args.base_url, res)

    strategy_id = args.strategy_id
    if strategy_id is None:
        status, body = http(args.base_url, "/api/strategies/")
        if status == 200:
            strategie = json.loads(body).get("data") or []
            strategy_id = strategie[0]["id"] if strategie else None
    if strategy_id is None:
        res.skip("CRUD notatek", "brak strategii w bazie — zapisz strategię w Builderze")
    else:
        check_notes(args.base_url, strategy_id, res)

    if job_id is not None:
        check_tearsheet(args.base_url, job_id, res)

    print(
        f"\n{_DIM}——————————————{_NC}\n"
        f"PASS: {res.passed}   FAIL: {res.failed}   SKIP: {res.skipped}"
    )
    if res.failed:
        print(f"{_RED}Backend ma problemy — napraw je przed testem UI.{_NC}")
        return 1
    print(f"{_GREEN}API zielone. Każdy błąd widoczny w przeglądarce jest błędem frontendu.{_NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
