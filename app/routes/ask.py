from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field, field_validator

from app.config import app_config
from app.services import (
    DocumentIdsEmptyError,
    DocumentIdsNotFoundError,
    EmbeddingGenerationError,
    ScopeRequiredError,
    answer_question,
    classify_question,
    get_current_user_id,
    get_relevant_documents,
    get_session,
    is_session_expired,
)
from app.utils import (
    AppError,
    AppErrorType,
    dedupe_document_ids,
    limiter,
    normalize_question,
)

router = APIRouter()

USER_ID_DEPENDENCY = Depends(get_current_user_id)
ASK_QUESTION_MAX_LENGTH = 1000
ASK_TOP_K_MAX = 20
ASK_DOCUMENT_IDS_MAX = 20

class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=ASK_QUESTION_MAX_LENGTH,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=ASK_TOP_K_MAX,
    )
    session_id: UUID | None = None
    document_ids: list[UUID] | None = None

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return normalize_question(value)

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, value: list[UUID] | None) -> list[UUID] | None:
        return dedupe_document_ids(value, max_items=ASK_DOCUMENT_IDS_MAX)


@router.post("/ask", status_code=status.HTTP_200_OK)
@limiter.limit(app_config.rate_limit_ask)
def ask_question(
    request: Request,
    payload: AskRequest,
    user_id: UUID | None = USER_ID_DEPENDENCY,
):

    question, top_k, session_id, document_ids = (
        payload.question,
        payload.top_k,
        payload.session_id,
        payload.document_ids,
    )

    if user_id and session_id:
        raise AppError(AppErrorType.SESSION_ID_NOT_ALLOWED)

    if not user_id and not session_id:
        raise AppError(AppErrorType.SESSION_ID_REQUIRED)

    if not user_id and session_id:
        session_record = get_session(session_id)
        if not session_record:
            raise AppError(AppErrorType.SESSION_NOT_FOUND)
        if is_session_expired(session_record):
            raise AppError(AppErrorType.SESSION_EXPIRED)

    classification = classify_question(question)
    if not classification.is_valid:
        raise AppError(AppErrorType.QUESTION_INVALID)

    try:
        docs = get_relevant_documents(
            query=question,
            k=top_k,
            session_id=session_id,
            user_id=user_id,
            document_ids=document_ids,
        )
    except DocumentIdsEmptyError as error:
        raise AppError(AppErrorType.DOCUMENT_IDS_EMPTY) from error
    except ScopeRequiredError as error:
        raise AppError(AppErrorType.SESSION_ID_REQUIRED) from error
    except DocumentIdsNotFoundError as error:
        raise AppError(AppErrorType.DOCUMENT_IDS_NOT_FOUND) from error
    except EmbeddingGenerationError as error:
        raise AppError(AppErrorType.EMBEDDING_FAILED) from error

    if not docs:
        raise AppError(AppErrorType.NO_RELEVANT_CONTEXT)

    context = "\n\n".join(doc.page_content for doc in docs)
    answer = answer_question(question, context)
    return {"answer": answer}