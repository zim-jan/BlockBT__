
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import OperationalError
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.session import get_session
from app.models.orm import AppSetting
from app.services.auth import decode_access_token

# Paths always public (even with auth_enabled=true)
_PUBLIC_PATHS = ("/api/health", "/api/auth/login", "/api/auth/auth-status", "/docs", "/openapi.json", "/redoc")


def is_auth_enabled() -> bool:
    """Check 'auth_enabled' key in AppSetting. Default: False.

    Fail-closed: gdy odczyt ustawienia się nie powiedzie (np. `database is
    locked`), zakładamy, że auth **jest** włączony. Zwracanie False oznaczałoby,
    że dowolny błąd SQLite wyłącza autoryzację całej aplikacji.

    Jedyny wyjątek to brak samej tabeli — baza nie przeszła jeszcze `init_db()`,
    więc nie ma w niej ani ustawień, ani kont. Nie ma czego chronić, a fail-closed
    zwracałby 401 na każdym żądaniu do końca życia procesu.
    """
    try:
        with get_session() as db:
            row = db.get(AppSetting, "auth_enabled")
            return row is not None and row.value.lower() == "true"
    except OperationalError as e:
        if "no such table" in str(e.orig).lower():
            logger.debug(f"Schemat bazy nie jest zainicjalizowany — auth traktowany jako wyłączony: {e.orig}")
            return False
        logger.error(f"Nie udało się odczytać ustawienia auth_enabled — fail-closed: {e}")
        return True
    except Exception as e:  # noqa: BLE001 — decyzja bezpieczeństwa, nie kontrola przepływu
        logger.error(f"Nie udało się odczytać ustawienia auth_enabled — fail-closed: {e}")
        return True


class AuthMiddleware(BaseHTTPMiddleware):
    """Conditional JWT auth. Skip entirely when auth_enabled=false."""

    async def dispatch(self, request: Request, call_next):
        # Public paths — always pass
        if any(request.url.path.startswith(p) for p in _PUBLIC_PATHS):
            request.state.user_id = None
            request.state.user_role = None
            return await call_next(request)

        # Auth disabled — phantom user
        if not is_auth_enabled():
            request.state.user_id = None
            request.state.user_role = None
            return await call_next(request)

        # Auth enabled — validate Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"},
            )

        try:
            payload = decode_access_token(auth_header[7:])
            request.state.user_id = int(payload["sub"])
            request.state.user_role = payload.get("role", "user")
        except Exception as e:
            logger.debug(f"JWT validation failed: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        return await call_next(request)
