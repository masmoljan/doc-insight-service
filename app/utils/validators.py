from uuid import UUID

from .messages import ValidationMessages


def normalize_question(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(ValidationMessages.QUESTION_EMPTY)
    return cleaned


def dedupe_document_ids(
    value: list[UUID] | None,
    *,
    max_items: int,
) -> list[UUID] | None:
    if value is None:
        return None
    if len(value) > max_items:
        raise ValueError(
            ValidationMessages.DOCUMENT_IDS_TOO_MANY.format(max_items=max_items)
        )
    seen: set[UUID] = set()
    deduped: list[UUID] = []
    for item in value:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
