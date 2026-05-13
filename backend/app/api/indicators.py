from __future__ import annotations

from fastapi import APIRouter

from app.schemas.base import ApiResponse
from app.services.engine.indicator_registry import IndicatorRegistry, initialize_registry
from app.services.engine.runner import vbt  # Using the vbt instance from runner

router = APIRouter()

# Initialize on first import of the router
initialize_registry(vbt)

@router.get("/", summary="List all available indicators", response_model=ApiResponse[list[dict]])
def list_indicators() -> ApiResponse[list[dict]]:
    """Return all technical indicators available in the registry."""
    # Ensure it's up to date
    indicators = IndicatorRegistry.get_all()
    # Remove function objects before sending to frontend
    data = []
    for ind in indicators:
        data.append({
            "name": ind["name"],
            "library": ind["library"],
            "params": ind["params"]
        })
    return ApiResponse(success=True, data=data)
