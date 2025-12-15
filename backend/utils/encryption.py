import hashlib
import re
from pathlib import Path
from cryptography.fernet import Fernet
from typing import List, Dict, Optional


class DataMasker:
    """Класс для маскирования конфиденциальных данных"""
    
    @staticmethod
    def mask_value(value: str, data_type: str) -> str:
        """Маскирует значение в зависимости от типа данных"""
        
        if data_type == "CREDIT_CARD":
            clean = re.sub(r'\D', '', value)
            if len(clean) >= 4:
                return f"****-****-****-{clean[-4:]}"
            return "****-****-****-****"
        
        elif data_type == "PHONE":
            clean = re.sub(r'\D', '', value)
            if len(clean) >= 2:
                return f"+7 (***) ***-**-{clean[-2:]}"
            return "+7 (***) ***-**-**"
        
        elif data_type == "EMAIL":
            parts = value.split("@")
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                if len(username) > 0:
                    masked_username = username[0] + "*" * (len(username) - 1)
                    return f"{masked_username}@{domain}"
            return "***@***.***"
        
        elif data_type == "INN":
            if len(value) >= 2:
                return f"{value[:2]}********"
            return "**********"
        
        elif data_type == "SNILS":
            if len(value) >= 2:
                return f"***-***-*** {value[-2:]}"
            return "***-***-*** **"
        
        elif data_type == "PASSPORT":
            return "** ** ******"
        
        elif data_type == "CORPORATE_SECRET":
            return "[КОРПОРАТИВНАЯ ИНФОРМАЦИЯ СКРЫТА]"
        
        return "*" * min(len(value), 10)
    
    @staticmethod
    def mask_text(text: str, findings: List[Dict]) -> str:
        """Маскирует все найденные конфиденциальные данные в тексте"""
        
        sorted_findings = sorted(findings, key=lambda x: x.get("start", 0), reverse=True)
        
        masked_text = text
        for finding in sorted_findings:
            start = finding.get("start")
            end = finding.get("end")
            data_type = finding.get("type")
            
            if start is not None and end is not None:
                masked_value = DataMasker.mask_value(
                    finding.get("value", ""), 
                    data_type
                )
                masked_text = (
                    masked_text[:start] + 
                    masked_value + 
                    masked_text[end:]
                )
        
        return masked_text


class EncryptionService:
    """Класс для шифрования конфиденциальных данных"""
    
    def __init__(self, key_path: str = None):
        self.key_path = Path(key_path) if key_path else None
        self.key: Optional[bytes] = None
        self.cipher: Optional[Fernet] = None
        
        if self.key_path:
            self._load_or_generate_key(self.key_path)
        else:
            self.key = Fernet.generate_key()
            self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self, key_path: Path) -> None:
        """Загружает существующий ключ или генерирует новый"""
        if key_path.exists():
            with key_path.open("rb") as f:
                self.key = f.read().strip()
        else:
            self.key = Fernet.generate_key()
            self._save_key_to_file(key_path)
        
        self.cipher = Fernet(self.key)
    
    def _save_key_to_file(self, key_path: Path) -> None:
        """Сохраняет ключ в файл"""
        key_path.parent.mkdir(parents=True, exist_ok=True)
        with key_path.open("wb") as f:
            f.write(self.key)
    
    def encrypt(self, data: str) -> str:
        """Шифрует данные"""
        if not data:
            return ""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Дешифрует данные"""
        if not encrypted_data:
            return ""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception:
            return "[Ошибка дешифрования]"
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Создаёт необратимый хеш данных (для индексации без раскрытия)"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def encrypt_findings(self, findings: List[Dict]) -> List[Dict]:
        """Шифрует конфиденциальные значения в списке findings"""
        encrypted_findings = []
        
        for finding in findings:
            encrypted_finding = finding.copy()
            
            if "value" in encrypted_finding:
                del encrypted_finding["value"]
            
            if "value" in finding:
                encrypted_finding["value_hash"] = self.hash_data(finding["value"])
            
            encrypted_findings.append(encrypted_finding)
        
        return encrypted_findings
