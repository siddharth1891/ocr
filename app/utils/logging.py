from __future__ import annotations

import logging
import re


logger = logging.getLogger("ocr")
logging.basicConfig(level=logging.INFO)


def mask_phi(text: str) -> str:
    text = re.sub(r"(Name\s*:\s*)([^\n]+)", r"\1***", text, flags=re.IGNORECASE)
    text = re.sub(r"(Age\s*:\s*)([^\n]+)", r"\1***", text, flags=re.IGNORECASE)
    text = re.sub(r"(Sex\s*:\s*)([^\n]+)", r"\1***", text, flags=re.IGNORECASE)
    return text
