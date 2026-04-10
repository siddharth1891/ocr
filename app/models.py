from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class OCRWord(BaseModel):
    text: str
    confidence: float
    bbox: dict[str, int]


class OCRLine(BaseModel):
    page_no: int
    line_no: int
    text: str
    confidence: float
    bbox: dict[str, int]
    words: list[OCRWord] = Field(default_factory=list)


class ParsedRow(BaseModel):
    test_name: str
    original_result: str
    parsed_result: str
    units: str | None = None
    reference_range: str | None = None
    page_no: int
    row_index: int
    confidence: float
    low_confidence: bool
    consistency_flags: list[str] = Field(default_factory=list)
    source_text: str


class SectionData(BaseModel):
    section_name: str
    rows: list[ParsedRow] = Field(default_factory=list)


class PatientMetadata(BaseModel):
    name: str | None = None
    age: str | None = None
    sex: str | None = None
    report_no: str | None = None
    date: str | None = None
    sample_no: str | None = None
    collected: str | None = None


class PageData(BaseModel):
    page_no: int
    lines: list[OCRLine]


class ReportDocument(BaseModel):
    document_id: str
    filename: str
    mime_type: str
    status: JobStatus
    patient_metadata: PatientMetadata
    pages: list[PageData]
    sections: list[SectionData]
    unknown_lines: list[str] = Field(default_factory=list)
    raw_text: str


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus
    error: str | None = None
    result: ReportDocument | None = None
