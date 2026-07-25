
import time

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.auth_middleware import is_auth_enabled
from app.core.user_scope import require_admin
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.base import ApiResponse
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter()

# --------------------------------------------------------------------------
# Rate limiting logowania (P1-5)
#
# Licznik w pamięci procesu — świadomie bez nowej zależności ani Redisa:
# BlockBT jest instancją single-process, a celem jest utrudnienie zgadywania
# hasła, nie ochrona przed rozproszonym atakiem. Restart API czyści licznik.
# --------------------------------------------------------------------------
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 60.0
_login_attempts: dict[tuple[str, str], list[float]] = {}


def _enforce_login_rate_limit(client_ip: str, username: str) -> None:
    """Raise 429 po przekroczeniu limitu prób dla pary (IP, username)."""
    now = time.monotonic()

    # Sprzątanie wygasłych kluczy — bez tego słownik rośnie w nieskończoność
    # przy zmiennych nazwach użytkownika (enumeracja).
    for key, stamps in list(_login_attempts.items()):
        if all(now - t >= _LOGIN_WINDOW_SECONDS for t in stamps):
            del _login_attempts[key]

    key = (client_ip, username)
    recent = [t for t in _login_attempts.get(key, []) if now - t < _LOGIN_WINDOW_SECONDS]

    if len(recent) >= _LOGIN_MAX_ATTEMPTS:
        _login_attempts[key] = recent
        retry_after = int(_LOGIN_WINDOW_SECONDS - (now - min(recent))) + 1
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    recent.append(now)
    _login_attempts[key] = recent


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(request: Request, request_data: LoginRequest) -> ApiResponse[LoginResponse]:
    """Authenticate and return JWT."""
    client_ip = request.client.host if request.client else "unknown"
    _enforce_login_rate_limit(client_ip, request_data.username)

    with get_session() as db:
        user = db.scalar(select(User).where(User.username == request_data.username))
        if not user or not verify_password(request_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is disabled")

        token = create_access_token(user.id, user.username, user.role)

        return ApiResponse(
            success=True,
            data=LoginResponse(
                access_token=token,
                user_id=user.id,
                username=user.username,
                role=user.role,
            ),
        )


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_current_user(request: Request) -> ApiResponse[UserResponse]:
    """Return current user info from token (or default local user when auth is disabled)."""
    if not is_auth_enabled():
        import datetime
        return ApiResponse(
            success=True,
            data=UserResponse(
                id=0,
                username="local",
                role="admin",
                is_active=True,
                created_at=datetime.datetime.now(datetime.UTC).isoformat(),
            ),
        )

    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    with get_session() as db:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return ApiResponse(
            success=True,
            data=UserResponse(
                id=user.id,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
            )
        )


@router.get("/users", response_model=ApiResponse[list[UserResponse]])
def list_users(request: Request) -> ApiResponse[list[UserResponse]]:
    """List all users (admin only)."""
    require_admin(request)
    
    with get_session() as db:
        users = db.scalars(select(User).order_by(User.id)).all()
        return ApiResponse(
            success=True,
            data=[
                UserResponse(
                    id=u.id,
                    username=u.username,
                    role=u.role,
                    is_active=u.is_active,
                    created_at=u.created_at.isoformat(),
                ) for u in users
            ]
        )


@router.post("/users", response_model=ApiResponse[UserResponse])
def create_user(request: Request, user_data: UserCreate) -> ApiResponse[UserResponse]:
    """Create a new user (admin only)."""
    require_admin(request)
    
    with get_session() as db:
        existing_user = db.scalar(select(User).where(User.username == user_data.username))
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
            
        new_user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return ApiResponse(
            success=True,
            data=UserResponse(
                id=new_user.id,
                username=new_user.username,
                role=new_user.role,
                is_active=new_user.is_active,
                created_at=new_user.created_at.isoformat(),
            )
        )


@router.put("/users/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(request: Request, user_id: int, user_data: UserUpdate) -> ApiResponse[UserResponse]:
    """Update a user (admin only)."""
    require_admin(request)
    
    with get_session() as db:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if user_data.username is not None:
            # Check if new username is already taken
            if user_data.username != user.username:
                existing = db.scalar(select(User).where(User.username == user_data.username))
                if existing:
                    raise HTTPException(status_code=400, detail="Username already taken")
            user.username = user_data.username
            
        if user_data.password is not None:
            user.password_hash = hash_password(user_data.password)
            
        if user_data.role is not None:
            user.role = user_data.role
            
        if user_data.is_active is not None:
            # Prevent deactivating self
            current_user_id = getattr(request.state, "user_id", None)
            if current_user_id == user_id and not user_data.is_active:
                raise HTTPException(status_code=400, detail="Cannot deactivate own account")
            user.is_active = user_data.is_active
            
        db.commit()
        db.refresh(user)
        
        return ApiResponse(
            success=True,
            data=UserResponse(
                id=user.id,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
            )
        )


@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
def delete_user(request: Request, user_id: int) -> ApiResponse[dict]:
    """Delete a user (admin only)."""
    require_admin(request)
    
    current_user_id = getattr(request.state, "user_id", None)
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete own account")
        
    with get_session() as db:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        db.delete(user)
        db.commit()
        
        return ApiResponse(success=True, data={"message": "User deleted successfully"})


@router.get("/auth-status", response_model=ApiResponse[dict])
def get_auth_status() -> ApiResponse[dict]:
    """Check if authentication is enabled (public)."""
    return ApiResponse(
        success=True,
        data={"auth_enabled": is_auth_enabled()}
    )
