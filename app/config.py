from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    max_upload_size_bytes: int = 20 * 1024 * 1024
    allowed_mime_types: set[str] = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
    }
    temp_dir: Path = Path("/tmp/ocr/uploads")


settings = Settings()
