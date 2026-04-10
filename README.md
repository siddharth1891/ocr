# ocr

Medical report OCR API that accepts PDF/JPG/PNG, extracts report data, and returns downloadable JSON with row/column style structure.

## Features
- Upload PDF, JPG, PNG
- Multi-page PDF processing
- OCR with per-word and per-line confidence + bounding boxes
- Parsed medical rows with:
  - `test_name`, `original_result`, `parsed_result`, `units`, `reference_range`, `page_no`, `row_index`
- Raw text preservation (verbatim) and unknown-line fallback bucket
- Consistency flags: missing units, missing reference range, out-of-range values
- JSON download endpoint

## API
- `POST /api/v1/reports/upload` → returns `job_id`
- `GET /api/v1/reports/{job_id}` → status/result
- `GET /api/v1/reports/{job_id}/download` → JSON attachment
- `GET /health`

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Notes
- OCR engine uses `pytesseract`; system Tesseract binary must be installed.
- File validation includes MIME/type and max upload size (20MB).
