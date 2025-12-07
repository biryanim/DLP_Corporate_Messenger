import re
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IncidentSeverity(str, Enum):
    """Уровень серьёзности инцидента"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentAction(str, Enum):
    """Действие при обнаружении инцидента"""
    BLOCK = "BLOCK"              # Блокировать сообщение
    MASK = "MASK"                # Замаскировать данные
    NOTIFY = "NOTIFY"            # Отправить уведомление
    QUARANTINE = "QUARANTINE"    # Поместить в карантин


class IncidentDetector:
    """
    Детектор конфиденциальных данных.
    Проверяет текст на соответствие паттернам конфиденциальной информации.
    """
    
    def __init__(self):
        """Инициализация паттернов обнаружения"""
        self.patterns = self._initialize_patterns()
        logger.info("✅ Детектор инициализирован")
    
    def _initialize_patterns(self) -> Dict[str, Dict]:
        """
        Инициализация паттернов для обнаружения.
        
        Returns:
            Dict с конфигурацией паттернов
        """
        return {
            # ИНН - 10 цифр
            "INN": {
                "pattern": r"\b\d{10}\b",
                "description": "Индивидуальный номер налогоплательщика",
                "severity": IncidentSeverity.HIGH,
                "action": IncidentAction.BLOCK,
                "context_length": 20
            },
            
            # СНИЛС - 11 цифр через дефис
            "SNILS": {
                "pattern": r"\b\d{3}-\d{3}-\d{3}\s\d{2}\b",
                "description": "Страховой номер индивидуального лицевого счёта",
                "severity": IncidentSeverity.CRITICAL,
                "action": IncidentAction.BLOCK,
                "context_length": 20
            },
            
            # Номер кредитной карты (Visa, Mastercard, Amex)
            "CREDIT_CARD": {
                "pattern": r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
                "description": "Номер кредитной карты",
                "severity": IncidentSeverity.CRITICAL,
                "action": IncidentAction.BLOCK,
                "context_length": 30
            },
            
            # Номер паспорта (4 буквы + 6 цифр, русский паспорт)
            "PASSPORT": {
                "pattern": r"\b[А-Яа-я]{4}\s\d{6}\b",
                "description": "Номер паспорта",
                "severity": IncidentSeverity.HIGH,
                "action": IncidentAction.BLOCK,
                "context_length": 20
            },
            
            # Email адрес
            "EMAIL": {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "description": "Email адрес",
                "severity": IncidentSeverity.MEDIUM,
                "action": IncidentAction.MASK,
                "context_length": 25
            },
            
            # Номер телефона (российский)
            "PHONE": {
                "pattern": r"\b(?:\+7|8)\s?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b",
                "description": "Номер телефона",
                "severity": IncidentSeverity.MEDIUM,
                "action": IncidentAction.MASK,
                "context_length": 25
            },
            
            # Пароль (в явном виде в сообщении)
            "PASSWORD": {
                "pattern": r"(?:password|пароль|pwd|пароль)\s*[:=]\s*['\"]?(\S+)['\"]?",
                "description": "Пароль в явном виде",
                "severity": IncidentSeverity.CRITICAL,
                "action": IncidentAction.BLOCK,
                "context_length": 40,
                "flags": re.IGNORECASE
            },
            
            # API ключ
            "API_KEY": {
                "pattern": r"(?:api[_-]?key|apikey|api_secret|secret_key)\s*[:=]\s*['\"]([A-Za-z0-9]{20,})['\"]",
                "description": "API ключ",
                "severity": IncidentSeverity.CRITICAL,
                "action": IncidentAction.BLOCK,
                "context_length": 40,
                "flags": re.IGNORECASE
            },
            
            # IPv4 адрес (внутренние)
            "INTERNAL_IP": {
                "pattern": r"\b(?:192\.168|10\.|172\.(?:1[6-9]|2[0-9]|3))\.\d{1,3}\.\d{1,3}\b",
                "description": "Внутренний IP адрес",
                "severity": IncidentSeverity.LOW,
                "action": IncidentAction.NOTIFY,
                "context_length": 20
            }
        }
    
    def detect(
        self,
        text: str,
        user_id: str,
        channel_id: str
    ) -> List[Dict]:
        """
        Обнаружить инциденты в тексте.
        
        Args:
            text: Текст для проверки
            user_id: ID пользователя
            channel_id: ID канала
        
        Returns:
            List[Dict]: Список найденных инцидентов
        """
        incidents = []
        
        logger.debug(f"🔍 Сканирование текста от {user_id}")
        
        # Проверяем каждый паттерн
        for incident_type, config in self.patterns.items():
            pattern = config["pattern"]
            flags = config.get("flags", 0)
            
            # Ищем совпадения
            matches = re.finditer(pattern, text, flags)
            
            for match in matches:
                # Извлекаем контекст
                context = self._extract_context(text, match, config["context_length"])
                
                incident = {
                    "type": incident_type,
                    "description": config["description"],
                    "severity": config["severity"].value,
                    "action": config["action"].value,
                    "pattern": match.group(0),
                    "context": context,
                    "match_position": (match.start(), match.end()),
                    "user_id": user_id,
                    "channel_id": channel_id
                }
                
                incidents.append(incident)
                logger.warning(f"⚠️ Обнаружен {incident_type}: {match.group(0)}")
        
        return incidents
    
    def _extract_context(
        self,
        text: str,
        match,
        context_length: int = 30
    ) -> str:
        """
        Извлечь контекст вокруг найденного совпадения.
        
        Args:
            text: Полный текст
            match: Объект совпадения из re.finditer
            context_length: Длина контекста с каждой стороны
        
        Returns:
            str: Контекст
        """
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        
        context = text[start:end]
        
        # Добавляем многоточие если контекст обрезан
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context
    
    def batch_detect(self, texts: List[str], user_ids: List[str], channel_ids: List[str]) -> List[List[Dict]]:
        """
        Обнаружить инциденты в нескольких текстах.
        
        Args:
            texts: Список текстов
            user_ids: Список ID пользователей
            channel_ids: Список ID каналов
        
        Returns:
            List[List[Dict]]: Список списков инцидентов
        """
        return [
            self.detect(text, user_id, channel_id)
            for text, user_id, channel_id in zip(texts, user_ids, channel_ids)
        ]
