import json

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

QUESTION_CLASSIFIER_SYSTEM_PROMPT = """# Your Role
You validate user questions for a document Q&A system.

# Your Task
Return is_valid=true if the question is meaningful or requests a summary/overview
of the document contents. Mark invalid only if it is a placeholder (e.g. 'string',
'test'), a single token without context, nonsense, or unrelated to documents.

# Examples
Valid: 'What is contained within the document?'
Valid: 'Give me a summary of this document.'
Invalid: 'string'
Invalid: 'test'

# Response Format
Return ONLY valid JSON with this shape:
{ "is_valid": true/false }
"""

QUESTION_CLASSIFIER_SCHEMA = {
    "name": "question_classifier",
    "schema": {
        "type": "object",
        "properties": {
            "is_valid": {"type": "boolean"},
        },
        "required": ["is_valid"],
        "additionalProperties": False,
    },
}

QUESTION_CLASSIFIER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": QUESTION_CLASSIFIER_SCHEMA,
}

model = ChatOpenAI(
    model="gpt-4.1",
    temperature=0,
    top_p=1,
)


class QuestionClassifierResult(BaseModel):
    is_valid: bool


def build_classifier_message(question: str) -> list[tuple[str, str]]:
    return [("system", QUESTION_CLASSIFIER_SYSTEM_PROMPT), ("human", question)]


def classify_question(question: str) -> QuestionClassifierResult:
    try:
        response = model.invoke(
            build_classifier_message(question),
            response_format=QUESTION_CLASSIFIER_RESPONSE_FORMAT,
        )
    except Exception:
        return QuestionClassifierResult(is_valid=True)

    try:
        payload = json.loads(str(response.content))
        parsed = QuestionClassifierResult.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return QuestionClassifierResult(is_valid=True)

    return parsed
