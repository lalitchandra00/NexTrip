import os
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_FALLBACK_MODELS = "gemini-3.6-flash,gemini-flash-lite-latest,gemini-3.1-flash-lite"


def model_names() -> List[str]:
    primary = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip()
    raw = os.getenv("GEMINI_FALLBACK_MODELS", DEFAULT_FALLBACK_MODELS)
    candidates = [primary] + [name.strip() for name in raw.split(",")]
    seen = set()
    names = []
    for name in candidates:
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def create_chat_model(model_name: str, temperature: float = 0.3):
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature,
        request_timeout=float(os.getenv("LLM_REQUEST_TIMEOUT", "60")),
        retries=int(os.getenv("LLM_MAX_RETRIES", "1")),
    )


def structured_llm(schema, temperature: float = 0):
    models = [create_chat_model(name, temperature) for name in model_names()]
    runnables = [model.with_structured_output(schema) for model in models]
    primary = runnables[0]
    if len(runnables) == 1:
        return primary
    return primary.with_fallbacks(runnables[1:])
