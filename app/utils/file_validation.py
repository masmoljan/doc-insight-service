ALLOWED_CONTENT_TYPES = {"application/pdf"}


def is_allowed_content_type(content_type: str) -> bool:
    return content_type in ALLOWED_CONTENT_TYPES or content_type.startswith("image/")
