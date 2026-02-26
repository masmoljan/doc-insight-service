import io
from typing import Any

import easyocr
import fitz
import numpy as np
import pymupdf4llm
from PIL import Image

from app.services.errors import TextExtractionError, UnsupportedContentTypeError
from app.utils import ErrorMessages

reader = easyocr.Reader(["en"])


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, dict[str, Any]]:
    doc = None
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        metadata = {
            "page_count": doc.page_count,
            "content_type": doc.metadata.get("content_type"),
        }
        text = pymupdf4llm.to_markdown(doc) or ""

        if not text.strip():
            ocr_pages = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                page_bytes = pix.tobytes("png")
                page_text, _ = extract_text_from_image(page_bytes)
                if page_text.strip():
                    ocr_pages.append(page_text)
            text = "\n\n".join(ocr_pages)

        return text, metadata
    except Exception as error:
        raise TextExtractionError from error
    finally:
        if doc is not None:
            doc.close()


def extract_text_from_image(file_bytes: bytes) -> tuple[str, dict[str, Any]]:
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img_format = img.format
            image = img.convert("RGB")
            image_np = np.array(image)
            texts = reader.readtext(image_np, detail=0)
            text = "\n".join(texts)
            return text, {
                "width": image.width,
                "height": image.height,
                "format": img_format,
            }
    except Exception as error:
        raise TextExtractionError from error


def extract_text(
    file_bytes: bytes,
    content_type: str | None,
) -> tuple[str, dict[str, Any]]:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if content_type and content_type.startswith("image/"):
        return extract_text_from_image(file_bytes)
    raise UnsupportedContentTypeError(
        ErrorMessages.UNSUPPORTED_CONTENT_TYPE.format(content_type=content_type)
    )
