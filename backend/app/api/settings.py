
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db.session import get_session
from app.models.orm import AppSetting, SystemPrompt
from app.schemas.settings import AppSettingUpdate, SystemPromptCreate, SystemPromptResponse

router = APIRouter()


@router.get("/")
def get_all_settings() -> dict[str, str]:
    """Get all global application settings."""
    with get_session() as db:
        settings = db.execute(select(AppSetting)).scalars().all()
        return {s.key: s.value for s in settings}


@router.put("/")
def update_settings(update: AppSettingUpdate) -> dict[str, str]:
    """Bulk update application settings."""
    with get_session() as db:
        updated_keys = []
        for key, value in update.model_dump(exclude_unset=True).items():
            if value is not None:
                setting = db.get(AppSetting, key)
                if not setting:
                    setting = AppSetting(key=key, value=str(value))
                    db.add(setting)
                else:
                    setting.value = str(value)
                updated_keys.append(key)
        
        db.commit()
        
        # Return the new state
        settings = db.execute(select(AppSetting)).scalars().all()
        return {s.key: s.value for s in settings}


@router.get("/prompts", response_model=list[SystemPromptResponse])
def list_system_prompts() -> list[SystemPromptResponse]:
    """List all system prompts."""
    with get_session() as db:
        prompts = db.execute(select(SystemPrompt).order_by(SystemPrompt.created_at)).scalars().all()
        return prompts  # type: ignore


@router.post("/prompts", response_model=SystemPromptResponse)
def create_system_prompt(payload: SystemPromptCreate) -> SystemPromptResponse:
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
        return prompt  # type: ignore


@router.put("/prompts/{prompt_id}", response_model=SystemPromptResponse)
def update_system_prompt(prompt_id: int, payload: SystemPromptCreate) -> SystemPromptResponse:
    """Update an existing system prompt."""
    with get_session() as db:
        prompt = db.get(SystemPrompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="System prompt not found")
        
        prompt.name = payload.name
        prompt.content = payload.content
        db.commit()
        db.refresh(prompt)
        return prompt  # type: ignore


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


@router.post("/prompts/{prompt_id}/default", response_model=SystemPromptResponse)
def set_default_prompt(prompt_id: int) -> SystemPromptResponse:
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
        return prompt  # type: ignore
