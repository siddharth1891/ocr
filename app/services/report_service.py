from __future__ import annotations

import uuid
from fastapi import UploadFile

from app.models import JobStatus, ReportDocument
from app.services.file_processor import file_processor
from app.services.ocr_service import ocr_service
from app.services.parser_service import parser_service
from app.storage import job_store
from app.utils.logging import logger, mask_phi


class ReportService:
    async def process_upload(self, file: UploadFile) -> str:
        job_id = str(uuid.uuid4())
        job_store.create(job_id)

        try:
            content = await file_processor.validate_and_read(file)
            images = file_processor.to_images(content, file.content_type or "")
            lines = ocr_service.extract_lines(images)
            metadata, pages, sections, unknown, raw_text = parser_service.parse(lines)

            result = ReportDocument(
                document_id=job_id,
                filename=file.filename or "uploaded_file",
                mime_type=file.content_type or "application/octet-stream",
                status=JobStatus.completed,
                patient_metadata=metadata,
                pages=pages,
                sections=sections,
                unknown_lines=unknown,
                raw_text=raw_text,
            )
            logger.info("Processed report: %s", mask_phi(raw_text[:500]))
            job_store.complete(job_id, result)
        except Exception as exc:  # noqa: BLE001
            job_store.fail(job_id, str(exc))

        return job_id


report_service = ReportService()
