from uuid import UUID


class DocumentIdsNotFoundError(Exception):
    def __init__(self, missing_ids: set[UUID]) -> None:
        self.missing_ids = missing_ids


class DocumentIdsEmptyError(Exception):
    pass


class ScopeRequiredError(Exception):
    pass


class UnsupportedContentTypeError(Exception):
    pass


class TextExtractionError(Exception):
    pass


class EmbeddingGenerationError(Exception):
    pass
