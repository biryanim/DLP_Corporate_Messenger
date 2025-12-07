from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Сервис для шифрования и расшифровки конфиденциальных данных.
    Использует Fernet (симметричное шифрование AES-128).
    """
    
    def __init__(self, key_path: Optional[str] = None, password: Optional[str] = None):
        """
        Инициализация сервиса шифрования.
        
        Args:
            key_path: Путь к файлу с ключом шифрования
            password: Пароль для генерации ключа (если key_path не указан)
        """
        self.key_path = key_path
        self.cipher = None
        
        if key_path:
            self._load_key_from_file(key_path)
        elif password:
            self._generate_key_from_password(password)
        else:
            self._generate_new_key()
        
        logger.info("✅ Сервис шифрования инициализирован")
    
    def _generate_new_key(self):
        """Генерировать новый ключ шифрования"""
        key = Fernet.generate_key()
        self.cipher = Fernet(key)
        logger.info("🔑 Новый ключ шифрования сгенерирован")
    
    def _generate_key_from_password(self, password: str):
        """
        Генерировать ключ из пароля.
        
        Args:
            password: Пароль для генерации ключа
        """
        # Используем PBKDF2 для генерации ключа из пароля
        salt = b'dlp_messenger_salt'  # В production использовать случайный salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = kdf.derive(password.encode())
        key = base64.urlsafe_b64encode(derived_key)
        
        self.cipher = Fernet(key)
        logger.info("🔑 Ключ шифрования сгенерирован из пароля")
    
    def _load_key_from_file(self, key_path: str):
        """
        Загрузить ключ из файла.
        
        Args:
            key_path: Путь к файлу с ключом
        """
        try:
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    key = f.read()
                self.cipher = Fernet(key)
                logger.info(f"🔑 Ключ загружен из {key_path}")
            else:
                logger.warning(f"⚠️ Файл ключа не найден: {key_path}")
                self._generate_new_key()
                self._save_key_to_file(key_path)
        
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке ключа: {str(e)}")
            raise
    
    def _save_key_to_file(self, key_path: str):
        """
        Сохранить ключ в файл.
        
        Args:
            key_path: Путь для сохранения ключа
        """
        try:
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            with open(key_path, 'wb') as f:
                f.write(self.cipher.key)
            logger.info(f"💾 Ключ сохранён в {key_path}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении ключа: {str(e)}")
            raise
    
    def encrypt(self, plaintext: str) -> str:
        """
        Зашифровать текст.
        
        Args:
            plaintext: Исходный текст
        
        Returns:
            str: Зашифрованный текст (base64)
        """
        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode())
            encrypted_str = base64.b64encode(encrypted_bytes).decode('utf-8')
            return encrypted_str
        
        except Exception as e:
            logger.error(f"❌ Ошибка при шифровании: {str(e)}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Расшифровать текст.
        
        Args:
            ciphertext: Зашифрованный текст (base64)
        
        Returns:
            str: Исходный текст
        """
        try:
            encrypted_bytes = base64.b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            return decrypted_str
        
        except Exception as e:
            logger.error(f"❌ Ошибка при расшифровании: {str(e)}")
            raise
    
    def encrypt_dict(self, data: dict, keys_to_encrypt: list = None) -> dict:
        """
        Зашифровать указанные ключи в словаре.
        
        Args:
            data: Словарь данных
            keys_to_encrypt: Список ключей для шифрования
        
        Returns:
            dict: Словарь с зашифрованными значениями
        """
        encrypted_data = data.copy()
        
        if keys_to_encrypt:
            for key in keys_to_encrypt:
                if key in encrypted_data:
                    encrypted_data[key] = self.encrypt(str(encrypted_data[key]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, keys_to_decrypt: list = None) -> dict:
        """
        Расшифровать указанные ключи в словаре.
        
        Args:
            data: Словарь данных
            keys_to_decrypt: Список ключей для расшифровки
        
        Returns:
            dict: Словарь с расшифрованными значениями
        """
        decrypted_data = data.copy()
        
        if keys_to_decrypt:
            for key in keys_to_decrypt:
                if key in decrypted_data:
                    try:
                        decrypted_data[key] = self.decrypt(decrypted_data[key])
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось расшифровать ключ {key}: {str(e)}")
        
        return decrypted_data
