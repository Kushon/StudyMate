from loguru import logger

SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}


async def parse(content: bytes, filename: str) -> str:
    """
    Dispatch to the correct parser based on file extension.
    Returns extracted plain text.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}. Allowed: {SUPPORTED_EXTENSIONS}")

    logger.info(f"Parsing {filename} as .{ext}")

    if ext == "pdf":
        from app.parsers.pdf import parse_pdf
        return parse_pdf(content)

    elif ext in ("docx", "doc"):
        from app.parsers.docx import parse_docx
        return parse_docx(content)

    else:  # txt
        text = content.decode("utf-8", errors="ignore")
        logger.info(f"TXT extracted {len(text)} characters")
        return text
