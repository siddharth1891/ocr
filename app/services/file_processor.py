from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.config import settings


class FileProcessor:
    def __init__(self) -> None:
        settings.temp_dir.mkdir(parents=True, exist_ok=True)

    async def validate_and_read(self, file: UploadFile) -> bytes:
        if file.content_type not in settings.allowed_mime_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(status_code=413, detail="File too large")
        return content

    def to_images(self, content: bytes, mime_type: str) -> list[Image.Image]:
        if mime_type == "application/pdf":
            return self._pdf_to_images(content)
        return [Image.open(BytesIO(content)).convert("RGB")]

    def _pdf_to_images(self, content: bytes) -> list[Image.Image]:
        pages: list[Image.Image] = []
        with fitz.open(stream=content, filetype="pdf") as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=250)
                mode = "RGBA" if pix.alpha else "RGB"
                pages.append(Image.frombytes(mode, [pix.width, pix.height], pix.samples).convert("RGB"))
        if not pages:
            raise HTTPException(status_code=400, detail="PDF contains no pages")
        return pages


file_processor = FileProcessor()
