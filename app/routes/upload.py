from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.config import app_config
from app.services import (
    EmbeddingGenerationError,
    TextExtractionError,
    UnsupportedContentTypeError,
    create_session,
    extract_text,
    get_current_user_id,
    get_session,
    insert_documents_with_chunks,
    is_session_expired,
)
from app.utils import (
    AppError,
    AppErrorType,
    ErrorMessages,
    ResponseMessages,
    is_allowed_content_type,
    limiter,
)

router = APIRouter()

FILES_PARAM = File(...)
USER_ID_DEPENDENCY = Depends(get_current_user_id)
MAX_FILENAME_LENGTH = 255


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit(app_config.rate_limit_upload)
async def upload_files(
    request: Request,
    files: list[UploadFile] = FILES_PARAM,
    session_id: UUID | None = None,
    user_id: UUID | None = USER_ID_DEPENDENCY,
):
    if not files:
        raise AppError(AppErrorType.NO_FILES_PROVIDED)
    if len(files) > app_config.upload_max_files:
        raise AppError(
            AppErrorType.TOO_MANY_FILES,
            message=ErrorMessages.MAX_FILES.format(
                max_files=app_config.upload_max_files
            ),
        )
    if user_id:
        session_id = None
    elif session_id is None:
        session_id = create_session().id
    else:
        session_record = get_session(session_id)
        if not session_record:
            raise AppError(AppErrorType.SESSION_NOT_FOUND)
        if is_session_expired(session_record):
            raise AppError(AppErrorType.SESSION_EXPIRED)

    extracted_documents: list[dict[str, Any]] = []

    for file in files:
        if not file.content_type:
            raise AppError(AppErrorType.CONTENT_TYPE_REQUIRED)
        if not is_allowed_content_type(file.content_type):
            raise AppError(
                AppErrorType.UNSUPPORTED_CONTENT_TYPE,
                message=ErrorMessages.UNSUPPORTED_CONTENT_TYPE.format(
                    content_type=file.content_type
                ),
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise AppError(
                AppErrorType.EMPTY_FILE,
                message=ErrorMessages.EMPTY_FILE.format(filename=file.filename),
            )
        if len(file_bytes) > app_config.upload_max_file_size_bytes:
            raise AppError(
                AppErrorType.FILE_TOO_LARGE,
                message=ErrorMessages.FILE_TOO_LARGE.format(filename=file.filename),
            )

        try:
            text, pdf_metadata = extract_text(file_bytes, file.content_type)
        except UnsupportedContentTypeError as error:
            raise AppError(
                AppErrorType.UNSUPPORTED_CONTENT_TYPE,
                message=str(error),
            ) from error
        except TextExtractionError as error:
            raise AppError(
                AppErrorType.NO_TEXT_EXTRACTED,
                message=ErrorMessages.FAILED_TO_EXTRACT_TEXT.format(
                    filename=file.filename
                ),
            ) from error

        if not text.strip():
            raise AppError(
                AppErrorType.NO_TEXT_EXTRACTED,
                message=ErrorMessages.NO_TEXT_EXTRACTED.format(
                    filename=file.filename
                ),
            )

        filename = Path(file.filename or "unknown").name.strip() or "unknown"
        if len(filename) > MAX_FILENAME_LENGTH:
            filename = filename[:MAX_FILENAME_LENGTH]
        extracted_documents.append(
            {
                "filename": filename,
                "content_type": file.content_type,
                "text": text,
                "metadata": pdf_metadata,
            }
        )

    document_metadata = [
        {
            "filename": extracted_doc["filename"],
            "content_type": extracted_doc["content_type"],
        }
        for extracted_doc in extracted_documents
    ]
    document_texts = [extracted_doc["text"] for extracted_doc in extracted_documents]
    try:
        inserted_document_ids = insert_documents_with_chunks(
            session_id=session_id,
            user_id=user_id,
            metadata_list=document_metadata,
            texts=document_texts,
        )
    except EmbeddingGenerationError as error:
        raise AppError(AppErrorType.EMBEDDING_FAILED) from error

    response = {
        "message": ResponseMessages.FILES_UPLOADED,
        "document_ids": [str(document_id) for document_id in inserted_document_ids],
    }
    if not user_id:
        response["session_id"] = str(session_id)

    return response


