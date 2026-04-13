import io
import pdfplumber
from loguru import logger


def parse_pdf(content: bytes) -> str:
    pages_text = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        logger.info(f"PDF has {len(pdf.pages)} pages")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                pages_text.append(text)
            else:
                logger.debug(f"Page {i + 1}: no extractable text (possibly scanned image)")

    result = "\n\n".join(pages_text)
    logger.info(f"PDF extracted {len(result)} characters from {len(pages_text)} pages")
    return result
