from __future__ import annotations

import json
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from app.models import JobStatus
from app.services.report_service import report_service
from app.storage import job_store

app = FastAPI(title="Medical Report OCR API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/reports/upload")
async def upload_report(file: UploadFile = File(...)) -> dict[str, str]:
    job_id = await report_service.process_upload(file)
    return {"job_id": job_id}


@app.get("/api/v1/reports/{job_id}")
def get_report(job_id: str):
    rec = job_store.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")

    if rec.status == JobStatus.failed:
        return JSONResponse(status_code=500, content={"job_id": job_id, "status": rec.status, "error": rec.error})

    if rec.status != JobStatus.completed:
        return {"job_id": job_id, "status": rec.status}

    return {"job_id": job_id, "status": rec.status, "result": rec.result.model_dump()}


@app.get("/api/v1/reports/{job_id}/download")
def download_report(job_id: str):
    rec = job_store.get(job_id)
    if not rec or rec.status != JobStatus.completed or not rec.result:
        raise HTTPException(status_code=404, detail="Completed report not found")

    payload = json.dumps(rec.result.model_dump(), ensure_ascii=False, indent=2)
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="report-{job_id}.json"'},
    )
