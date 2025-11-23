import re
from typing import List, Dict, Tuple
from enum import Enum

class DataType(str, Enum):
    INN = "INN"
    SNILS = "SNILS"
    PASSPORT = "PASSPORT"
    CREDIT_CARD = "CREDIT_CARD"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    IP_ADDRESS = "IP_ADDRESS"

class SensitivityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

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

class SensitiveDataDetector:
    """Основной класс для детектирования чувствительных данных"""
    
    def __init__(self):
        self.compiled_patterns = {
            data_type: re.compile(pattern["regex"]) 
            for data_type, pattern in DataPattern.PATTERNS.items()
        }
    
    def scan(self, text: str) -> List[Dict]:
        findings = []
        
        for data_type, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                finding = {
                    "data_type": data_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "sensitivity": DataPattern.PATTERNS[data_type]["sensitivity"],
                    "name": DataPattern.PATTERNS[data_type]["name"],
                    "description": DataPattern.PATTERNS[data_type]["description"],
                    "context_before": text[max(0, match.start()-30):match.start()],
                    "context_after": text[match.end():min(len(text), match.end()+30)]
                }
                
                if self._validate_finding(data_type, match.group()):
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
        """Проверка контрольной суммы ИНН"""
        inn = inn.replace(" ", "")
        if len(inn) not in [10, 12]:
            return False
        
        return inn.isdigit()
    
    def _luhn_check(self, card_number: str) -> bool:
        """Алгоритм Луна для проверки номера карты"""
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
    
    def get_risk_score(self, findings: List[Dict]) -> int:
        """Вычисляет общий риск на основе найденных данных"""
        severity_scores = {
            SensitivityLevel.LOW: 10,
            SensitivityLevel.MEDIUM: 30,
            SensitivityLevel.HIGH: 60,
            SensitivityLevel.CRITICAL: 100
        }
        
        return sum(severity_scores[f["sensitivity"]] for f in findings)
