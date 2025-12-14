from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ScanRequest(BaseModel):
    """Модель запроса для сканирования"""
    text: str = Field(..., description="Текст для сканирования", min_length=1)
    user_id: str = Field(..., description="ID пользователя")
    channel_id: str = Field(..., description="ID канала/чата")
    metadata: Optional[dict] = Field(None, description="Дополнительные метаданные")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Мой номер карты: 4532 1234 5678 9010",
                "user_id": "john_doe",
                "channel_id": "general",
                "metadata": {"source": "slack"}
            }
        }


class IncidentResponse(BaseModel):
    """Модель ответа для отдельного инцидента"""
    id: str = Field(..., description="ID документа в Elasticsearch")
    timestamp: str = Field(..., description="Время обнаружения")
    user_id: str = Field(..., description="ID пользователя")
    channel_id: str = Field(..., description="ID канала")
    incident_type: str = Field(..., description="Тип инцидента (ИНН, карта, и т.д.)")
    severity: str = Field(..., description="Серьёзность (low, medium, high, critical)")
    pattern_matched: str = Field(..., description="Обнаруженный паттерн")
    action: str = Field(..., description="Действие (BLOCK, MASK, NOTIFY, QUARANTINE)")
    status: str = Field("open", description="Статус (open, resolved, false_positive)")
    is_encrypted: bool = Field(False, description="Зашифровано ли содержимое")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "incident_001",
                "timestamp": "2025-12-07T22:00:00Z",
                "user_id": "john_doe",
                "channel_id": "general",
                "incident_type": "CREDIT_CARD",
                "severity": "high",
                "pattern_matched": "****",
                "action": "BLOCK",
                "status": "open",
                "is_encrypted": True
            }
        }


class ScanResponse(BaseModel):
    """Модель ответа сканирования"""
    scan_id: str
    timestamp: str
    user_id: str
    channel_id: str
    incidents_found: bool
    incidents_count: int
    incidents: List[dict]


class IncidentModel(BaseModel):
    """Модель инцидента в БД"""
    id: Optional[str] = None
    timestamp: datetime
    user_id: str
    channel_id: str
    incident_type: str
    severity: str
    pattern_matched: str
    original_text_encrypted: str
    action: str
    status: str = "open"
    is_encrypted: bool = True
    
    class Config:
        from_attributes = True
