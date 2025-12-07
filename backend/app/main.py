from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from typing import List, Optional
import os
from dotenv import load_dotenv

from backend.utils.detector import IncidentDetector
from backend.utils.encryption import EncryptionService
from backend.services.elasticsearch_service import ElasticsearchService
from backend.models.incident import IncidentModel, ScanRequest, IncidentResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

detector: Optional[IncidentDetector] = None
encryption_service: Optional[EncryptionService] = None
es_service: Optional[ElasticsearchService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detector, encryption_service, es_service
    
    try:
        logger.info("🚀 Инициализация сервисов...")
        
        detector = IncidentDetector()
        encryption_service = EncryptionService(
            key_path=os.getenv('ENCRYPTION_KEY_PATH', 'app/keys/encryption.key')
        )
        es_service = ElasticsearchService(
            hosts=[os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')]
        )
        
        if not es_service.is_connected():
            logger.warning("⚠️ Не удалось подключиться к Elasticsearch")
        else:
            logger.info("✅ Elasticsearch подключен")
        
        logger.info("✅ Все сервисы инициализированы")
    
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {str(e)}")
        raise
    
    yield
    
    try:
        logger.info("🛑 Очистка ресурсов...")
        if es_service:
            es_service.close()
        logger.info("✅ Ресурсы очищены")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке: {str(e)}")


app = FastAPI(
    title="DLP Messenger Control API",
    description="API для контроля утечек данных в мессенджерах",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    es_status = "connected" if es_service and es_service.is_connected() else "disconnected"
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "detector": "ready" if detector else "not_ready",
            "encryption": "ready" if encryption_service else "not_ready",
            "elasticsearch": es_status
        }
    }


@app.post("/api/v1/scan", response_model=dict)
async def scan_message(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Асинхронный эндпоинт для сканирования текста на конфиденциальные данные.
    
    - Проверяет текст детектором
    - При обнаружении инцидента шифрует содержимое
    - Сохраняет JSON в Elasticsearch в фоне
    
    Args:
        request: ScanRequest с полями text, user_id, channel_id
        background_tasks: BackgroundTasks для асинхронной обработки
    
    Returns:
        dict с результатами сканирования
    """
    
    if not detector or not encryption_service or not es_service:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        logger.info(f"📥 Сканирование текста от пользователя {request.user_id}")
        
        incidents = detector.detect(
            text=request.text,
            user_id=request.user_id,
            channel_id=request.channel_id
        )
        
        response_data = {
            "scan_id": f"scan_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": request.user_id,
            "channel_id": request.channel_id,
            "incidents_found": len(incidents) > 0,
            "incidents_count": len(incidents),
            "incidents": []
        }
        
        if incidents:
            logger.info(f"🚨 Обнаружено {len(incidents)} инцидентов")
            
            for incident in incidents:
                encrypted_text = encryption_service.encrypt(request.text)
                encrypted_context = encryption_service.encrypt(incident.get('context', ''))
                
                incident_doc = {
                    "scan_id": response_data["scan_id"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": request.user_id,
                    "channel_id": request.channel_id,
                    "incident_type": incident.get('type', 'unknown'),
                    "severity": incident.get('severity', 'medium'),
                    "pattern_matched": incident.get('pattern', ''),
                    "original_text": encrypted_text,  
                    "context": encrypted_context,     
                    "action": incident.get('action', 'NOTIFY'),
                    "is_encrypted": True,
                    "status": "open"
                }
                
                response_data["incidents"].append({
                    "incident_type": incident.get('type'),
                    "severity": incident.get('severity'),
                    "action": incident.get('action'),
                    "pattern": incident.get('pattern', '***')
                })
                
                background_tasks.add_task(
                    save_incident_to_elasticsearch,
                    incident_doc
                )
            
            logger.info(f"✅ Инциденты обработаны и отправлены в очередь")
        else:
            logger.info("✅ Конфиденциальные данные не обнаружены")
        
        return response_data
    
    except Exception as e:
        logger.error(f"❌ Ошибка при сканировании: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")


async def save_incident_to_elasticsearch(incident_doc: dict):
    """
    Асинхронно сохраняет инцидент в Elasticsearch
    """
    try:
        logger.info(f"💾 Сохранение инцидента в Elasticsearch: {incident_doc['scan_id']}")
        
        if es_service and es_service.is_connected():
            result = es_service.index_document(
                index="dlp-incidents",
                document=incident_doc,
                doc_id=incident_doc.get('scan_id')
            )
            logger.info(f"✅ Инцидент сохранён: {result}")
        else:
            logger.warning("⚠️ Elasticsearch недоступен, инцидент не сохранён")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в Elasticsearch: {str(e)}")


@app.get("/api/v1/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "timestamp",
    order: str = "desc",
    severity: Optional[str] = None,
    user_id: Optional[str] = None,
    incident_type: Optional[str] = None
):
    """
    Получить список инцидентов из Elasticsearch с фильтрацией и сортировкой.
    
    Args:
        limit: Максимальное количество результатов (по умолчанию 50)
        offset: Смещение от начала (по умолчанию 0)
        sort_by: Поле для сортировки (timestamp, severity, user_id)
        order: Порядок сортировки (asc, desc)
        severity: Фильтр по серьёзности (low, medium, high, critical)
        user_id: Фильтр по ID пользователя
        incident_type: Фильтр по типу инцидента
    
    Returns:
        List[IncidentResponse]: Список инцидентов
    """
    
    if not es_service or not es_service.is_connected():
        raise HTTPException(status_code=503, detail="Elasticsearch is not available")
    
    try:
        logger.info(f"📊 Запрос инцидентов: limit={limit}, offset={offset}, sort_by={sort_by}")
        
        filters = {}
        
        if severity:
            filters['severity'] = severity
        
        if user_id:
            filters['user_id'] = user_id
        
        if incident_type:
            filters['incident_type'] = incident_type
        
        incidents = es_service.search_incidents(
            index="dlp-incidents",
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"✅ Получено {len(incidents)} инцидентов")
        
        response_incidents = []
        for incident in incidents:
            try:
                if incident.get('is_encrypted') and encryption_service:
                    decrypted_text = encryption_service.decrypt(incident.get('original_text', ''))
                else:
                    decrypted_text = incident.get('original_text', '')
                
                response_incidents.append(IncidentResponse(
                    id=incident.get('_id', 'unknown'),
                    timestamp=incident.get('timestamp', datetime.utcnow().isoformat()),
                    user_id=incident.get('user_id', 'unknown'),
                    channel_id=incident.get('channel_id', 'unknown'),
                    incident_type=incident.get('incident_type', 'unknown'),
                    severity=incident.get('severity', 'medium'),
                    pattern_matched=incident.get('pattern_matched', '***'),
                    action=incident.get('action', 'NOTIFY'),
                    status=incident.get('status', 'open'),
                    is_encrypted=incident.get('is_encrypted', False)
                ))
            
            except Exception as e:
                logger.warning(f"⚠️ Ошибка обработки инцидента: {str(e)}")
                continue
        
        return response_incidents
    
    except Exception as e:
        logger.error(f"❌ Ошибка при получении инцидентов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching incidents: {str(e)}")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "name": "DLP Messenger Control API",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs",
        "endpoints": {
            "health": "GET /health",
            "scan": "POST /api/v1/scan",
            "incidents": "GET /api/v1/incidents"
        }
    }