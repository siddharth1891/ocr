from __future__ import annotations

import re
from app.models import OCRLine, PageData, ParsedRow, PatientMetadata, SectionData


class ParserService:
    _meta_map = {
        "name": "name",
        "age": "age",
        "sex": "sex",
        "report no": "report_no",
        "date": "date",
        "sample no": "sample_no",
        "collected": "collected",
    }

    def parse(self, lines: list[OCRLine]) -> tuple[PatientMetadata, list[PageData], list[SectionData], list[str], str]:
        metadata = self._extract_metadata(lines)
        pages = self._to_pages(lines)
        sections, unknown = self._extract_sections(lines)
        raw_text = "\n".join(line.text for line in lines)
        return metadata, pages, sections, unknown, raw_text

    def _to_pages(self, lines: list[OCRLine]) -> list[PageData]:
        by_page: dict[int, list[OCRLine]] = {}
        for line in lines:
            by_page.setdefault(line.page_no, []).append(line)
        return [PageData(page_no=page, lines=page_lines) for page, page_lines in sorted(by_page.items())]

    def _extract_metadata(self, lines: list[OCRLine]) -> PatientMetadata:
        metadata = PatientMetadata()
        for line in lines:
            parts = re.split(r"\s*:\s*", line.text, maxsplit=1)
            if len(parts) != 2:
                continue
            key, value = parts[0].strip().lower(), parts[1].strip()
            for alias, field in self._meta_map.items():
                if alias in key and value:
                    setattr(metadata, field, value)
                    break
        return metadata

    def _extract_sections(self, lines: list[OCRLine]) -> tuple[list[SectionData], list[str]]:
        sections: list[SectionData] = []
        unknown: list[str] = []
        current_section = SectionData(section_name="UNCLASSIFIED", rows=[])
        row_idx = 0

        for line in lines:
            txt = line.text.strip()
            if not txt:
                continue
            if self._is_metadata_line(txt):
                continue
            if self._is_section_header(txt):
                if current_section.rows:
                    sections.append(current_section)
                current_section = SectionData(section_name=txt, rows=[])
                row_idx = 0
                continue

            row = self._parse_row(txt, line, row_idx)
            if row:
                current_section.rows.append(row)
                row_idx += 1
            elif not self._is_layout_noise(txt):
                unknown.append(txt)

        if current_section.rows:
            sections.append(current_section)
        return sections, unknown

    def _is_section_header(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in [
                "complete blood count",
                "bio-chemical",
                "cbc",
                "differential",
                "report",
            ]
        ) and len(text.split()) <= 8

    def _is_layout_noise(self, text: str) -> bool:
        lowered = text.lower()
        return any(token in lowered for token in ["test name", "result", "units", "reference", "end of report", "page"])

    def _is_metadata_line(self, text: str) -> bool:
        parts = re.split(r"\s*:\s*", text, maxsplit=1)
        if len(parts) != 2:
            return False
        key = parts[0].strip().lower()
        return any(alias in key for alias in self._meta_map)

    def _parse_row(self, text: str, line: OCRLine, row_idx: int) -> ParsedRow | None:
        # Expected shape: "Hemoglobin 17.0 g/dl 12-16"
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned.split()) < 2:
            return None

        numeric_tokens = list(re.finditer(r"[-+]?\d*\.?\d+", cleaned))
        if not numeric_tokens:
            return None

        result_match = numeric_tokens[0]
        test_name = cleaned[: result_match.start()].strip(" :-")
        rest = cleaned[result_match.end() :].strip()
        result_value = result_match.group(0)

        unit_match = re.match(r"^([%a-zA-Z/\.]+)", rest)
        units = unit_match.group(1) if unit_match else None
        reference_range = None
        range_match = re.search(r"(\d*\.?\d+)\s*[-–—]\s*(\d*\.?\d+)", rest)
        if range_match:
            reference_range = f"{range_match.group(1)}-{range_match.group(2)}"

        if not test_name:
            return None

        flags = self._consistency_flags(result_value, units, reference_range)
        low_confidence = line.confidence < 70.0
        return ParsedRow(
            test_name=test_name,
            original_result=result_value,
            parsed_result=result_value,
            units=units,
            reference_range=reference_range,
            page_no=line.page_no,
            row_index=row_idx,
            confidence=line.confidence,
            low_confidence=low_confidence,
            consistency_flags=flags,
            source_text=text,
        )

    def _consistency_flags(self, result_value: str, units: str | None, reference_range: str | None) -> list[str]:
        flags: list[str] = []
        try:
            value = float(result_value)
        except ValueError:
            return ["invalid_result_value"]

        if not units:
            flags.append("missing_unit")

        if reference_range:
            try:
                low_s, high_s = reference_range.split("-")
                low, high = float(low_s), float(high_s)
                if value < low or value > high:
                    flags.append("out_of_reference_range")
            except ValueError:
                flags.append("invalid_reference_range")
        else:
            flags.append("missing_reference_range")

        return flags


parser_service = ParserService()
