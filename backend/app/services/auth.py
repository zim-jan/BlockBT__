
import datetime
import secrets
from typing import Any

import bcrypt
import jwt
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings

_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_HOURS = 24


def hash_password(plain: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plaintext against bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Create JWT access token."""
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=_JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[_JWT_ALGORITHM])


def ensure_admin_user(db: Session) -> bool:
    """Zaseeduj pierwsze konto admina, jeśli w bazie nie ma żadnego użytkownika.

    Wywoływane w dwóch miejscach, które muszą zachować się identycznie:
      * `lifespan` przy starcie API (auth już włączony),
      * `PUT /api/settings/` w momencie **włączania** auth — bez tego właściciel
        instancji zamyka się na zewnątrz do czasu restartu procesu (P0-1b).

    Zwraca True, jeśli konto zostało utworzone.
    """
    from app.models.user import User  # import lokalny — unika cyklu app.models ↔ app.services

    if db.query(User).count() > 0:
        return False

    password = settings.ADMIN_PASSWORD
    generated = password is None
    if generated:
        password = secrets.token_urlsafe(16)

    db.add(
        User(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(password),
            role="admin",
        )
    )
    db.commit()

    if generated:
        # Jedyny moment, w którym hasło jest widoczne — nie da się go odczytać później.
        logger.warning(
            "Utworzono konto administratora "
            f"'{settings.ADMIN_USERNAME}' z wygenerowanym hasłem: {password}\n"
            "Zapisz je teraz i zmień po pierwszym logowaniu "
            "(ustaw ADMIN_PASSWORD w .env, aby wskazać własne)."
        )
    else:
        logger.info(f"Utworzono konto administratora '{settings.ADMIN_USERNAME}' (hasło z konfiguracji).")

    return True
