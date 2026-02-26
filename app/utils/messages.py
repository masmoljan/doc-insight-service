class ResponseMessages:
    FILES_UPLOADED = "Files uploaded successfully"
    HEALTH_OK = "Document ingestion service is available."


class ErrorMessages:
    MAX_FILES = "Maximum number of files is {max_files}"
    UNSUPPORTED_CONTENT_TYPE = "Unsupported content type: {content_type}"
    EMPTY_FILE = "Empty file: {filename}"
    FILE_TOO_LARGE = "File too large: {filename}"
    FAILED_TO_EXTRACT_TEXT = "Failed to extract text from: {filename}"
    NO_TEXT_EXTRACTED = "No text extracted from: {filename}"


class ValidationMessages:
    QUESTION_EMPTY = "question must not be empty"
    DOCUMENT_IDS_TOO_MANY = "document_ids cannot exceed {max_items} items"
