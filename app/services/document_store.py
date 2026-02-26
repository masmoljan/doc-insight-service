from uuid import UUID

from langchain_core.documents import Document as LCDocument
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlmodel import Session, select

from app.config import app_config
from app.database import engine
from app.models import Document, EmbeddedDocument
from app.services.embedding_cache import (
    build_doc_chunk_key,
    get_embeddings,
    set_embedding,
)
from app.utils import decrypt, encrypt
from app.services.errors import (
    EmbeddingGenerationError,
    DocumentIdsEmptyError,
    DocumentIdsNotFoundError,
    ScopeRequiredError,
)

openAIEmbeddings = OpenAIEmbeddings(model="text-embedding-3-small")


def build_embedded_records(
    documents: list[tuple[UUID, str]],
) -> list[EmbeddedDocument]:
    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    records: list[EmbeddedDocument] = []

    for document_id, text in documents:
        document = LCDocument(page_content=text)
        final_docs = text_splitter.split_documents([document]) or [document]

        for i, doc_chunk in enumerate(final_docs):
            doc_chunk.metadata["chunk_index"] = i
            doc_chunk.metadata["chunk_count"] = len(final_docs)

        contents = [d.page_content for d in final_docs]
        cache_keys = [build_doc_chunk_key(content) for content in contents]
        cached_embeddings = get_embeddings(cache_keys)
        if None in cached_embeddings:
            try:
                embeddings = openAIEmbeddings.embed_documents(contents)
            except Exception as error:
                raise EmbeddingGenerationError from error
            for index, embedding in enumerate(embeddings):
                set_embedding(
                    cache_keys[index],
                    embedding,
                    app_config.embedding_cache_doc_ttl_seconds,
                )
        else:
            embeddings = cached_embeddings
        records.extend(
            EmbeddedDocument(
                content=encrypt(doc_chunk.page_content),
                metadata_=doc_chunk.metadata or {},
                document_id=document_id,
                embedding=embedding,
            )
            for doc_chunk, embedding in zip(final_docs, embeddings, strict=True)
        )

    return records


def insert_documents(
    session_id: UUID | None,
    user_id: UUID | None,
    metadata_list: list[dict | None],
) -> list[UUID]:
    if not metadata_list:
        return []

    with Session(engine) as session:
        docs = [
            Document(
                session_id=session_id,
                user_id=user_id,
                metadata_=metadata or {},
            )
            for metadata in metadata_list
        ]
        session.add_all(docs)
        session.commit()
        for doc in docs:
            session.refresh(doc)
        return [doc.id for doc in docs]


def insert_document_chunks(documents: list[tuple[UUID, str]]) -> None:
    records = build_embedded_records(documents)
    if not records:
        return

    with Session(engine) as session:
        session.add_all(records)
        session.commit()


def insert_documents_with_chunks(
    session_id: UUID | None,
    user_id: UUID | None,
    metadata_list: list[dict | None],
    texts: list[str],
) -> list[UUID]:
    if not metadata_list:
        return []

    documents = [
        Document(
            session_id=session_id,
            user_id=user_id,
            metadata_=metadata or {},
        )
        for metadata in metadata_list
    ]
    documents_to_chunk = [
        (document.id, text)
        for document, text in zip(documents, texts, strict=True)
    ]
    records = build_embedded_records(documents_to_chunk)
    if not records:
        return []

    with Session(engine) as session:
        session.add_all(documents)
        session.add_all(records)
        session.commit()
        document_ids = [document.id for document in documents]

    return document_ids


def get_relevant_documents(
    query: str,
    k: int = 5,
    session_id: UUID | None = None,
    user_id: UUID | None = None,
    document_ids: list[UUID] | None = None,
) -> list[LCDocument]:
    if document_ids is not None and len(document_ids) == 0:
        raise DocumentIdsEmptyError

    if not session_id and not user_id:
        raise ScopeRequiredError

    with Session(engine) as session:
        if document_ids:
            requested_ids = set(document_ids)
            doc_statement = select(Document.id)
            if user_id:
                doc_statement = doc_statement.where(Document.user_id == user_id)
            else:
                doc_statement = doc_statement.where(
                    Document.session_id == session_id
                )
            doc_statement = doc_statement.where(Document.id.in_(requested_ids))
            existing_ids = set(session.exec(doc_statement).all())
            missing_ids = requested_ids - existing_ids
            if missing_ids:
                raise DocumentIdsNotFoundError(missing_ids)

        try:
            query_embedding = openAIEmbeddings.embed_query(query)
        except Exception as error:
            raise EmbeddingGenerationError from error
        statement = select(EmbeddedDocument).join(
            Document, EmbeddedDocument.document_id == Document.id
        )

        if user_id:
            statement = statement.where(Document.user_id == user_id)
        else:
            statement = statement.where(Document.session_id == session_id)

        if document_ids:
            statement = statement.where(Document.id.in_(document_ids))

        statement = statement.order_by(
            EmbeddedDocument.embedding.cosine_distance(query_embedding)
        ).limit(k)
        results = session.exec(statement).all()

    return [
        LCDocument(
            page_content=decrypt(row.content),
            metadata=dict(row.metadata_ or {}),
        )
        for row in results
    ]
