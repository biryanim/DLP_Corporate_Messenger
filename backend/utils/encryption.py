import hashlib
import re
from cryptography.fernet import Fernet
from typing import List, Dict

class DataMasker:
    """Класс для маскирования конфиденциальных данных"""
    
    @staticmethod
    def mask_value(value: str, data_type: str) -> str:
        """Маскирует значение в зависимости от типа данных"""
        
        if data_type == "CREDIT_CARD":
            clean = re.sub(r'\D', '', value)
            return f"****-****-****-{clean[-4:]}"
        
        elif data_type == "PHONE":
            clean = re.sub(r'\D', '', value)
            return f"+7 ({clean[1:4]}) ***-**-{clean[-2:]}"
        
        elif data_type == "EMAIL":
            parts = value.split("@")
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                masked_username = username[0] + "*" * (len(username) - 1)
                return f"{masked_username}@{domain}"
        
        elif data_type == "INN":
            return f"{value[:2]}********"
        
        elif data_type == "SNILS":
            return f"***-***-*** {value[-2:]}"
        
        return "*" * len(value)
    
    @staticmethod
    def mask_text(text: str, findings: List[Dict]) -> str:
        """Маскирует все найденные конфиденциальные данные в тексте"""
        
        sorted_findings = sorted(findings, key=lambda x: x["start"], reverse=True)
        
        masked_text = text
        for finding in sorted_findings:
            masked_value = DataMasker.mask_value(
                finding["value"], 
                finding["data_type"]
            )
            masked_text = (
                masked_text[:finding["start"]] + 
                masked_value + 
                masked_text[finding["end"]:]
            )
        
        return masked_text

class DataEncryption:
    """Класс для шифрования данных"""
    
    def __init__(self, key: bytes = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Шифрует данные"""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Дешифрует данные"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Создаёт необратимый хеш данных"""
        return hashlib.sha256(data.encode()).hexdigest()
