from fastapi import Header, HTTPException


def get_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    """
    Dependency to enforce API key authentication.
    For Phase 6, we use a static valid key that would normally be read from settings.
    """
    valid_key = "blockbt-secret-key-123"
    if not x_api_key or x_api_key != valid_key:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return x_api_key
