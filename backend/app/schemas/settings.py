from datetime import datetime

from pydantic import BaseModel


class AppSettingUpdate(BaseModel):
    data_connector: str | None = None
    vbtpro_path: str | None = None
    prefer_pro_engine: bool | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    parquet_cache_ttl_hours: int | None = None


class SystemPromptCreate(BaseModel):
    name: str
    content: str


from pydantic import BaseModel, ConfigDict

class SystemPromptResponse(BaseModel):
    id: int
    name: str
    content: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
