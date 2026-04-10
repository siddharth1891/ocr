from app.models import OCRLine, OCRWord
from app.services.parser_service import ParserService


def _line(text: str, conf: float = 90.0, page: int = 1, line_no: int = 1):
    return OCRLine(
        page_no=page,
        line_no=line_no,
        text=text,
        confidence=conf,
        bbox={"left": 0, "top": 0, "width": 100, "height": 10},
        words=[OCRWord(text="x", confidence=conf, bbox={"left": 0, "top": 0, "width": 1, "height": 1})],
    )


def test_parse_metadata_and_rows():
    parser = ParserService()
    lines = [
        _line("Name : Mr. ABHISHEK SHUKLA", line_no=1),
        _line("Age : 20 Yr", line_no=2),
        _line("Sex : Male", line_no=3),
        _line("Complete Blood Count", line_no=4),
        _line("Hemoglobin 17.0 g/dl 12-16", line_no=5),
        _line("Total Leukocyte Count 9800 /cmm 4000-11000", line_no=6),
    ]

    metadata, pages, sections, unknown, raw_text = parser.parse(lines)

    assert metadata.name == "Mr. ABHISHEK SHUKLA"
    assert metadata.age == "20 Yr"
    assert metadata.sex == "Male"
    assert len(pages) == 1
    assert len(sections) >= 1
    rows = sections[0].rows
    assert rows[0].test_name.lower() == "hemoglobin"
    assert rows[0].parsed_result == "17.0"
    assert rows[0].reference_range == "12-16"
    assert "out_of_reference_range" in rows[0].consistency_flags
    assert not unknown
    assert "Hemoglobin" in raw_text
