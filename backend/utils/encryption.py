from cryptography.fernet import Fernet
from pathlib import Path


class EncryptionService:
    def __init__(self, key_path: str):
        self.key_path = Path(key_path)
        self.key: bytes | None = None
        self.cipher: Fernet | None = None
        self._load_key_from_file(self.key_path)

    def _load_key_from_file(self, key_path: Path) -> None:
        if key_path.exists():
            with key_path.open("rb") as f:
                self.key = f.read().strip()
        else:
            # генерируем новый ключ
            self.key = Fernet.generate_key()
            # сохраняем его в файл
            self._save_key_to_file(key_path)

        # создаём Fernet из ключа
        self.cipher = Fernet(self.key)

    def _save_key_to_file(self, key_path: Path) -> None:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        with key_path.open("wb") as f:
            f.write(self.key)  # <-- Сохраняем bytes ключ, а не self.cipher.key

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()
