from __future__ import annotations

from collections import defaultdict

import pytesseract
from PIL import Image

from app.models import OCRLine, OCRWord


class OCRService:
    def extract_lines(self, images: list[Image.Image]) -> list[OCRLine]:
        lines: list[OCRLine] = []
        for page_idx, image in enumerate(images, start=1):
            lines.extend(self._extract_page_lines(image=image, page_no=page_idx))
        return lines

    def _extract_page_lines(self, image: Image.Image, page_no: int) -> list[OCRLine]:
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError("Tesseract OCR binary is not installed") from exc

        grouped: dict[tuple[int, int, int], list[OCRWord]] = defaultdict(list)
        n = len(data["text"])
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            if not txt:
                continue
            conf = float(data["conf"][i]) if str(data["conf"][i]).strip() not in {"", "-1"} else 0.0
            word = OCRWord(
                text=txt,
                confidence=max(conf, 0.0),
                bbox={
                    "left": int(data["left"][i]),
                    "top": int(data["top"][i]),
                    "width": int(data["width"][i]),
                    "height": int(data["height"][i]),
                },
            )
            key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
            grouped[key].append(word)

        output: list[OCRLine] = []
        for line_no, words in enumerate(grouped.values(), start=1):
            words = sorted(words, key=lambda w: w.bbox["left"])
            left = min(w.bbox["left"] for w in words)
            top = min(w.bbox["top"] for w in words)
            right = max(w.bbox["left"] + w.bbox["width"] for w in words)
            bottom = max(w.bbox["top"] + w.bbox["height"] for w in words)
            text = " ".join(w.text for w in words)
            conf = sum(w.confidence for w in words) / len(words)
            output.append(
                OCRLine(
                    page_no=page_no,
                    line_no=line_no,
                    text=text,
                    confidence=conf,
                    bbox={"left": left, "top": top, "width": right - left, "height": bottom - top},
                    words=words,
                )
            )
        return sorted(output, key=lambda l: (l.page_no, l.bbox["top"], l.bbox["left"]))


ocr_service = OCRService()
