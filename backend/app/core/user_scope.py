
import ipaddress

from fastapi import HTTPException, Request
from sqlalchemy import Select


def scoped_query(query: Select, model, request: Request) -> Select:
    """Add WHERE user_id=X when auth active. Passthrough when auth off (user_id=None)."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return query.where(model.user_id == user_id)
    return query


def get_user_id(request: Request) -> int | None:
    """Extract user_id from request state. None when auth disabled."""
    return getattr(request.state, "user_id", None)


def is_loopback(request: Request) -> bool:
    """True gdy żądanie przyszło z tej samej maszyny (127.0.0.0/8, ::1).

    Używane jako granica zaufania w trybie bez logowania — patrz `require_admin`.
    """
    client = request.client
    if client is None or not client.host:
        return False
    host = client.host
    # Adresy IPv4 tunelowane przez gniazdo IPv6 przychodzą jako ::ffff:127.0.0.1
    if host.startswith("::ffff:"):
        host = host[7:]
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        # Nazwa hosta zamiast IP (m.in. "testclient" ze starlette TestClient)
        return False


def require_admin(request: Request) -> None:
    """Raise 403 if the caller may not perform admin operations.

    Przy włączonym auth wymagana jest rola `admin`. Przy **wyłączonym** auth nie
    ma ról, więc granicą zaufania jest loopback: właściciel maszyny robi co chce,
    ale ktoś z LAN-u nie założy sobie konta admina ani nie przestawi ustawień
    (eskalacja: POST /api/auth/users → PUT /api/settings/ {auth_enabled: true}).
    """
    user_role = getattr(request.state, "user_role", None)
    if user_role is None:
        if is_loopback(request):
            return
        raise HTTPException(
            status_code=403,
            detail="Admin operations are restricted to localhost while authentication is disabled",
        )
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def verify_resource_access(resource, request: Request) -> None:
    """Verify current user owns the resource or is admin. No-op when auth disabled."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        return  # auth disabled
    user_role = getattr(request.state, "user_role", None)
    if user_role == "admin":
        return
    resource_user_id = getattr(resource, "user_id", None)
    # user_id IS NULL to zasoby sprzed Fazy 16 (lub sprzed backfillu migracji
    # 0001) — nie mają właściciela, więc widzi je wyłącznie admin.
    if resource_user_id is None or resource_user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: resource access denied")
