
from fastapi import Request
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


def require_admin(request: Request) -> None:
    """Raise 403 if current user is not admin. No-op when auth disabled."""
    from fastapi import HTTPException

    user_role = getattr(request.state, "user_role", None)
    if user_role is None:
        return  # auth disabled, no role check
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def verify_resource_access(resource, request: Request) -> None:
    """Verify current user owns the resource or is admin. No-op when auth disabled."""
    from fastapi import HTTPException

    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        return  # auth disabled
    user_role = getattr(request.state, "user_role", None)
    if user_role == "admin":
        return
    resource_user_id = getattr(resource, "user_id", None)
    if resource_user_id is not None and resource_user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: resource access denied")
