from dataclasses import dataclass
from enum import Enum

from fastapi import status

class AppErrorType(Enum):
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_ALREADY_EXISTS = "user_already_exists"
    SESSION_ID_REQUIRED = "session_id_required"
    SESSION_ID_NOT_ALLOWED = "session_id_not_allowed"
    SESSION_NOT_FOUND = "session_not_found"
    SESSION_EXPIRED = "session_expired"
    QUESTION_INVALID = "question_invalid"
    NO_RELEVANT_CONTEXT = "no_relevant_context"
    DOCUMENT_IDS_NOT_FOUND = "document_ids_not_found"
    DOCUMENT_IDS_EMPTY = "document_ids_empty"
    NO_FILES_PROVIDED = "no_files_provided"
    TOO_MANY_FILES = "too_many_files"
    CONTENT_TYPE_REQUIRED = "content_type_required"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    EMPTY_FILE = "empty_file"
    FILE_TOO_LARGE = "file_too_large"
    NO_TEXT_EXTRACTED = "no_text_extracted"
    EMBEDDING_FAILED = "embedding_failed"
    DATA_ENCRYPTION_KEY_INVALID = "data_encryption_key_invalid"
    DATA_ENCRYPTION_FAILED = "data_encryption_failed"
    DATA_DECRYPTION_FAILED = "data_decryption_failed"
    JWT_SECRET_MISSING = "jwt_secret_missing"
    TOKEN_MISSING_USER_ID = "token_missing_user_id"
    TOKEN_INVALID = "token_invalid"


@dataclass(frozen=True)
class AppErrorTemplate:
    http_status_code: int
    message: str
    code: str


_APP_ERROR_TEMPLATES: dict[AppErrorType, AppErrorTemplate] = {
    AppErrorType.INVALID_CREDENTIALS: AppErrorTemplate(
        http_status_code=status.HTTP_401_UNAUTHORIZED,
        message="Invalid credentials",
        code="401-01",
    ),
    AppErrorType.SESSION_EXPIRED: AppErrorTemplate(
        http_status_code=status.HTTP_401_UNAUTHORIZED,
        message="Session expired",
        code="401-02",
    ),
    AppErrorType.TOKEN_MISSING_USER_ID: AppErrorTemplate(
        http_status_code=status.HTTP_401_UNAUTHORIZED,
        message="Token missing 'user_id'",
        code="401-03",
    ),
    AppErrorType.TOKEN_INVALID: AppErrorTemplate(
        http_status_code=status.HTTP_401_UNAUTHORIZED,
        message="Invalid token",
        code="401-04",
    ),
    AppErrorType.SESSION_ID_REQUIRED: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="session_id is required for anonymous requests",
        code="400-01",
    ),
    AppErrorType.SESSION_ID_NOT_ALLOWED: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="session_id is not allowed for authenticated requests",
        code="400-05",
    ),
    AppErrorType.QUESTION_INVALID: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="Question is too vague or not about the documents",
        code="400-08",
    ),
    AppErrorType.NO_FILES_PROVIDED: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="No files provided",
        code="400-02",
    ),
    AppErrorType.TOO_MANY_FILES: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="Too many files",
        code="400-03",
    ),
    AppErrorType.EMPTY_FILE: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="Empty file",
        code="400-04",
    ),
    AppErrorType.USER_ALREADY_EXISTS: AppErrorTemplate(
        http_status_code=status.HTTP_409_CONFLICT,
        message="User with this email already exists",
        code="409-01",
    ),
    AppErrorType.SESSION_NOT_FOUND: AppErrorTemplate(
        http_status_code=status.HTTP_404_NOT_FOUND,
        message="Session not found",
        code="404-01",
    ),
    AppErrorType.NO_RELEVANT_CONTEXT: AppErrorTemplate(
        http_status_code=status.HTTP_404_NOT_FOUND,
        message="No relevant context found in specified documents",
        code="404-02",
    ),
    AppErrorType.DOCUMENT_IDS_NOT_FOUND: AppErrorTemplate(
        http_status_code=status.HTTP_404_NOT_FOUND,
        message="One or more document_ids were not found for this request",
        code="404-03",
    ),
    AppErrorType.DOCUMENT_IDS_EMPTY: AppErrorTemplate(
        http_status_code=status.HTTP_400_BAD_REQUEST,
        message="document_ids cannot be an empty list",
        code="400-06",
    ),
    AppErrorType.CONTENT_TYPE_REQUIRED: AppErrorTemplate(
        http_status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        message="File content type is required",
        code="415-01",
    ),
    AppErrorType.UNSUPPORTED_CONTENT_TYPE: AppErrorTemplate(
        http_status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        message="Unsupported content type",
        code="415-02",
    ),
    AppErrorType.FILE_TOO_LARGE: AppErrorTemplate(
        http_status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        message="File too large",
        code="413-01",
    ),
    AppErrorType.NO_TEXT_EXTRACTED: AppErrorTemplate(
        http_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="No text extracted from file",
        code="422-01",
    ),
    AppErrorType.EMBEDDING_FAILED: AppErrorTemplate(
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Embedding generation failed",
        code="500-02",
    ),
    AppErrorType.DATA_ENCRYPTION_KEY_INVALID: AppErrorTemplate(
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="DATA_ENCRYPTION_KEY must be 32 bytes",
        code="500-03",
    ),
    AppErrorType.DATA_ENCRYPTION_FAILED: AppErrorTemplate(
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Document content encryption failed",
        code="500-04",
    ),
    AppErrorType.DATA_DECRYPTION_FAILED: AppErrorTemplate(
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Document content decryption failed",
        code="500-05",
    ),
    AppErrorType.JWT_SECRET_MISSING: AppErrorTemplate(
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="JWT_SECRET is not set",
        code="500-01",
    ),
}


class AppError(Exception):
    def __init__(
        self,
        error_type: AppErrorType,
        *,
        message: str | None = None,
    ) -> None:
        super().__init__(error_type.value)
        self.type = error_type

        template = _APP_ERROR_TEMPLATES.get(error_type)
        if not template:
            template = AppErrorTemplate(
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Internal Server Error",
                code="500-01",
            )

        self.http_status_code = template.http_status_code
        self.body = {
            "code": template.code,
            "message": message or template.message,
        }
