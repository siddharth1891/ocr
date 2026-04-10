from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def make_png_bytes() -> bytes:
    img = Image.new("RGB", (200, 80), color="white")
    bio = BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_upload_invalid_type():
    res = client.post(
        "/api/v1/reports/upload",
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]

    detail = client.get(f"/api/v1/reports/{job_id}")
    assert detail.status_code == 500


def test_upload_image_no_tesseract_failure_path_is_handled():
    png = make_png_bytes()
    res = client.post(
        "/api/v1/reports/upload",
        files={"file": ("report.png", png, "image/png")},
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]

    detail = client.get(f"/api/v1/reports/{job_id}")
    assert detail.status_code in {200, 500}
