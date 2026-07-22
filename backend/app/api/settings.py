from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from typing import Any

from app.db.session import get_session
from app.models.orm import AppSetting, SystemPrompt
from app.schemas.base import ApiResponse
from app.schemas.settings import AppSettingUpdate, SystemPromptCreate, SystemPromptResponse
from app.services.mcp.llm_client import OllamaClient

router = APIRouter()


@router.get("/ollama/status", response_model=ApiResponse[dict[str, Any]])
async def get_ollama_status() -> ApiResponse[dict[str, Any]]:
    """Check Ollama connection health and model availability."""
    client = OllamaClient()
    status = await client.get_status()
    return ApiResponse(success=True, data=status)


@router.get("/", response_model=ApiResponse[dict[str, str]])
def get_all_settings() -> ApiResponse[dict[str, str]]:
    """Get all global application settings."""
    with get_session() as db:
        settings = db.execute(select(AppSetting)).scalars().all()
        data = {s.key: s.value for s in settings}
        return ApiResponse(success=True, data=data)


@router.put("/", response_model=ApiResponse[dict[str, str]])
def update_settings(update: AppSettingUpdate) -> ApiResponse[dict[str, str]]:
    """Bulk update application settings."""
    with get_session() as db:
        for key, value in update.model_dump(exclude_unset=True).items():
            if value is not None:
                setting = db.get(AppSetting, key)
                if not setting:
                    setting = AppSetting(key=key, value=str(value))
                    db.add(setting)
                else:
                    setting.value = str(value)
        
        db.commit()
        
        # Return the new state
        settings = db.execute(select(AppSetting)).scalars().all()
        data = {s.key: s.value for s in settings}
        return ApiResponse(success=True, data=data)


@router.get("/prompts", response_model=ApiResponse[list[SystemPromptResponse]])
def list_system_prompts() -> ApiResponse[list[SystemPromptResponse]]:
    """List all system prompts."""
    with get_session() as db:
        prompts = db.execute(select(SystemPrompt).order_by(SystemPrompt.created_at)).scalars().all()
        data = [SystemPromptResponse.model_validate(p) for p in prompts]
        return ApiResponse(success=True, data=data)


@router.post("/prompts", response_model=ApiResponse[SystemPromptResponse])
def create_system_prompt(payload: SystemPromptCreate) -> ApiResponse[SystemPromptResponse]:
    """Create a new system prompt."""
    with get_session() as db:
        # Check if there are any prompts at all, if not, make this the default
        count = db.query(SystemPrompt).count()
        is_default = count == 0
        
        prompt = SystemPrompt(
            name=payload.name,
            content=payload.content,
            is_default=is_default
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        data = SystemPromptResponse.model_validate(prompt)
        return ApiResponse(success=True, data=data)


@router.put("/prompts/{prompt_id}", response_model=ApiResponse[SystemPromptResponse])
def update_system_prompt(prompt_id: int, payload: SystemPromptCreate) -> ApiResponse[SystemPromptResponse]:
    """Update an existing system prompt."""
    with get_session() as db:
        prompt = db.get(SystemPrompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="System prompt not found")
        
        prompt.name = payload.name
        prompt.content = payload.content
        db.commit()
        db.refresh(prompt)
        data = SystemPromptResponse.model_validate(prompt)
        return ApiResponse(success=True, data=data)


@router.delete("/prompts/{prompt_id}", status_code=204)
def delete_system_prompt(prompt_id: int) -> None:
    """Delete a system prompt."""
    with get_session() as db:
        prompt = db.get(SystemPrompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="System prompt not found")
            
        if prompt.is_default:
            # If deleting the default, try to make another one default
            next_prompt = db.execute(
                select(SystemPrompt).where(SystemPrompt.id != prompt_id).limit(1)
            ).scalar_one_or_none()
            if next_prompt:
                next_prompt.is_default = True
                
        db.delete(prompt)
        db.commit()


@router.post("/prompts/{prompt_id}/default", response_model=ApiResponse[SystemPromptResponse])
def set_default_prompt(prompt_id: int) -> ApiResponse[SystemPromptResponse]:
    """Mark a system prompt as the default."""
    with get_session() as db:
        prompt = db.get(SystemPrompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="System prompt not found")
            
        # Unset previous default
        current_default = db.execute(
            select(SystemPrompt).where(SystemPrompt.is_default == True) # noqa: E712
        ).scalar_one_or_none()
        
        if current_default:
            current_default.is_default = False
            
        prompt.is_default = True
        db.commit()
        db.refresh(prompt)
        data = SystemPromptResponse.model_validate(prompt)
        return ApiResponse(success=True, data=data)
