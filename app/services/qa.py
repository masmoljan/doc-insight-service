import json

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

NO_ANSWER_TEXT = "I don't know based on the provided documents."

QA_SYSTEM_PROMPT = f"""# Your Role
You are a document Q&A assistant. Answer using ONLY the provided context.

# Your Task
1. Answer the user's question using the context.
2. If the answer is not in the context, respond with exactly:
{NO_ANSWER_TEXT}

# Response Format
Return ONLY valid JSON with this shape:
{{ "answer": "..." }}
"""

def build_qa_message(context: str, question: str) -> list[tuple[str, str]]:
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    return [("system", QA_SYSTEM_PROMPT), ("human", user_prompt)]

QA_JSON_SCHEMA = {
    "name": "qa_response",
    "schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
        },
        "required": ["answer"],
        "additionalProperties": False,
    },
}

QA_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": QA_JSON_SCHEMA,
}

model = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.3,
    top_p=1,
)

class QAResponseSchema(BaseModel):
    answer: str = Field(description="Final answer based on the context.")


def answer_question(question: str, context: str) -> str:
    try:
        qa_message_prompt = build_qa_message(context, question)
        response = model.invoke(
            qa_message_prompt,
            response_format=QA_RESPONSE_FORMAT,
        )
        print(response.response_metadata)
    except Exception:
        return NO_ANSWER_TEXT

    response_payload = str(response.content)
    try:
        payload = json.loads(response_payload)
        parsed = QAResponseSchema.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return NO_ANSWER_TEXT

    answer = parsed.answer.strip()
    if not answer:
        return NO_ANSWER_TEXT

    return answer