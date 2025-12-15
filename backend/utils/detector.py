import re
from typing import List, Dict, Optional
from enum import Enum


class DataType(str, Enum):
    INN = "INN"
    SNILS = "SNILS"
    PASSPORT = "PASSPORT"
    CREDIT_CARD = "CREDIT_CARD"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    IP_ADDRESS = "IP_ADDRESS"
    CORPORATE_SECRET = "CORPORATE_SECRET"


class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataPattern:
    """Паттерны для обнаружения конфиденциальных данных"""

    PATTERNS = {
        DataType.INN: {
            "regex": r"\b\d{10}(?:\d{2})?\b",
            "name": "ИНН",
            "sensitivity": SensitivityLevel.HIGH,
            "description": "Идентификационный номер налогоплательщика"
        },
        DataType.SNILS: {
            "regex": r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b",
            "name": "СНИЛС",
            "sensitivity": SensitivityLevel.HIGH,
            "description": "Страховой номер индивидуального лицевого счёта"
        },
        DataType.PASSPORT: {
            "regex": r"\b(?:\d{4}\s?\d{6}|\d{2}\s?\d{2}\s?\d{6})\b",
            "name": "Паспорт РФ",
            "sensitivity": SensitivityLevel.CRITICAL,
            "description": "Серия и номер паспорта"
        },
        DataType.CREDIT_CARD: {
            "regex": r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
            "name": "Банковская карта",
            "sensitivity": SensitivityLevel.CRITICAL,
            "description": "Номер банковской карты"
        },
        DataType.PHONE: {
            "regex": r"\+?7[\s-]?\(?(?:\d{3})\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}",
            "name": "Телефон",
            "sensitivity": SensitivityLevel.MEDIUM,
            "description": "Российский номер телефона"
        },
        DataType.EMAIL: {
            "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "name": "Email",
            "sensitivity": SensitivityLevel.MEDIUM,
            "description": "Адрес электронной почты"
        },
        DataType.IP_ADDRESS: {
            "regex": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "name": "IP адрес",
            "sensitivity": SensitivityLevel.LOW,
            "description": "IPv4 адрес"
        }
    }

    CORPORATE_BLACKLIST = [
        "конфиденциально",
        "секретно",
        "не для разглашения",
        "внутреннее использование",
        "коммерческая тайна",
        "служебная информация",
        "дсп",  # для служебного пользования
        "строго конфиденциально",
        "corporate confidential",
        "internal use only",
        "proprietary",
        "restricted"
    ]


class IncidentDetector:
    """Основной класс для детектирования чувствительных данных"""
    
    def __init__(self):
        self.compiled_patterns = {
            data_type: re.compile(pattern["regex"]) 
            for data_type, pattern in DataPattern.PATTERNS.items()
        }
        
        self.blacklist_patterns = [
            re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            for word in DataPattern.CORPORATE_BLACKLIST
        ]
    
    def detect(self, text: str, user_id: int = None, channel_id: int = None) -> List[Dict]:
        """
        Главный метод для обнаружения инцидентов.
        Совместим с текущим API backend.
        """
        findings = []
    
        for data_type, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                if self._validate_finding(data_type, match.group()):
                    finding = {
                        "type": data_type.value,
                        "severity": DataPattern.PATTERNS[data_type]["sensitivity"].value,
                        "pattern": DataPattern.PATTERNS[data_type]["name"],
                        "action": self._get_action(DataPattern.PATTERNS[data_type]["sensitivity"]),
                        "context": text[max(0, match.start()-30):min(len(text), match.end()+30)],
                        "value": match.group(),  # для внутреннего использования
                        "start": match.start(),
                        "end": match.end()
                    }
                    findings.append(finding)
        
        for pattern in self.blacklist_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                finding = {
                    "type": DataType.CORPORATE_SECRET.value,
                    "severity": SensitivityLevel.CRITICAL.value,
                    "pattern": "Корпоративное ключевое слово",
                    "action": "BLOCK",
                    "context": text[max(0, match.start()-30):min(len(text), match.end()+30)],
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                }
                findings.append(finding)
        
        return findings
    
    def _validate_finding(self, data_type: DataType, value: str) -> bool:
        """Дополнительная валидация для снижения false positives"""
        
        if data_type == DataType.INN:
            return self._validate_inn(value)
        elif data_type == DataType.CREDIT_CARD:
            return self._luhn_check(value.replace(" ", "").replace("-", ""))
        elif data_type == DataType.IP_ADDRESS:
            return self._validate_ip(value)
        
        return True
    
    def _validate_inn(self, inn: str) -> bool:
        """Проверка ИНН"""
        inn = inn.replace(" ", "")
        if len(inn) not in [10, 12]:
            return False
        return inn.isdigit()
    
    def _luhn_check(self, card_number: str) -> bool:
        """Алгоритм Луна для проверки номера карты"""
        if not card_number.isdigit():
            return False
        
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        
        return checksum % 10 == 0
    
    def _validate_ip(self, ip: str) -> bool:
        """Проверка валидности IP адреса"""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def _get_action(self, severity: SensitivityLevel) -> str:
        """Определяет действие на основе уровня серьёзности"""
        action_map = {
            SensitivityLevel.LOW: "NOTIFY",
            SensitivityLevel.MEDIUM: "MASK",
            SensitivityLevel.HIGH: "MASK",
            SensitivityLevel.CRITICAL: "BLOCK"
        }
        return action_map.get(severity, "NOTIFY")
    
    def get_risk_score(self, findings: List[Dict]) -> int:
        """Вычисляет общий риск на основе найденных данных"""
        severity_scores = {
            "low": 10,
            "medium": 30,
            "high": 60,
            "critical": 100
        }
        
        return sum(severity_scores.get(f.get("severity", "low"), 0) for f in findings)
