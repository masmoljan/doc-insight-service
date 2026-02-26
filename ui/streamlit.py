import os
import uuid

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MAX_FILES = 5
MAX_FILE_SIZE_MB = 10

for key, value in {
    "api_base": API_BASE_URL,
    "jwt_token": "",
    "session_id_input": "",
    "document_ids_input": "",
    "upload_error": "",
    "upload_status": None,
    "upload_response": None,
}.items():
    st.session_state.setdefault(key, value)


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def get_auth_headers() -> dict[str, str]:
    token_value = st.session_state.jwt_token.strip()
    return {"Authorization": f"Bearer {token_value}"} if token_value else {}

st.title("Document Ingestion Service")

with st.sidebar:
    st.subheader("API Config")
    st.text_input("API base URL", key="api_base")
    st.text_input("JWT token (optional)", type="password", key="jwt_token")

st.subheader("Upload Document(s)")
st.caption(
    f"Max {MAX_FILES} files per upload. "
    f"Max {MAX_FILE_SIZE_MB:g} MB per file."
)
st.file_uploader(
    "Upload PDFs or images",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="upload_files",
)

st.text_input(
    "Session ID (optional for anonymous flow)",
    key="session_id_input",
)

def handle_upload() -> None:
    st.session_state.upload_error = ""
    st.session_state.upload_status = None
    st.session_state.upload_response = None

    files = st.session_state.upload_files or []
    if not files:
        st.session_state.upload_error = "Please select at least one file."
        return

    files_payload = [
        ("files", (file.name, file.getvalue(), file.type))
        for file in files
    ]

    session_id_value = st.session_state.session_id_input.strip()
    data = {"session_id": session_id_value} if session_id_value else {}

    try:
        resp = requests.post(
            f"{st.session_state.api_base}/upload",
            files=files_payload,
            data=data,
            headers=get_auth_headers(),
            timeout=60,
        )
    except requests.RequestException as error:
        st.session_state.upload_error = f"Upload failed: {error}"
        return

    st.session_state.upload_status = resp.status_code
    try:
        payload = resp.json()
    except ValueError:
        st.session_state.upload_error = "Upload failed: response was not valid JSON."
        return

    st.session_state.upload_response = payload
    if resp.ok:
        session_id = payload.get("session_id")
        document_ids = payload.get("document_ids")
        if session_id:
            st.session_state.session_id_input = session_id
        if document_ids:
            st.session_state.document_ids_input = ", ".join(document_ids)

st.button("Upload", on_click=handle_upload)

if st.session_state.upload_error:
    st.error(st.session_state.upload_error)
if st.session_state.upload_status is not None:
    st.write(st.session_state.upload_status)
if st.session_state.upload_response is not None:
    st.json(st.session_state.upload_response)

st.subheader("Ask a question")
question = st.text_input("Question")
st.text_input(
    "Document IDs (comma-separated, optional)",
    key="document_ids_input",
)

if st.button("Ask") and question.strip():
    payload = {"question": question.strip()}

    if not st.session_state.jwt_token.strip():
        session_id_value = st.session_state.session_id_input.strip()
        if session_id_value:
            payload["session_id"] = session_id_value

    document_ids_value = st.session_state.document_ids_input.strip()
    if document_ids_value:
        raw_ids = [d.strip() for d in document_ids_value.split(",") if d.strip()]
        invalid_ids = [raw_id for raw_id in raw_ids if not is_valid_uuid(raw_id)]
        if invalid_ids:
            st.error(f"Invalid document ID(s): {', '.join(invalid_ids)}")
            st.stop()
        payload["document_ids"] = raw_ids

    headers = {"Content-Type": "application/json", **get_auth_headers()}

    resp = requests.post(
        f"{st.session_state.api_base}/ask",
        json=payload,
        headers=headers,
        timeout=60,
    )
    st.write(resp.status_code)
    st.json(resp.json())