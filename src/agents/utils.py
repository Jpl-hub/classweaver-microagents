import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import httpx
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from openai.types import CreateEmbeddingResponse


logger = logging.getLogger(__name__)

RETRYABLE_OPENAI_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)

NON_RETRYABLE_OPENAI_ERRORS = (
    AuthenticationError,
    BadRequestError,
)


class AgentInvocationError(RuntimeError):
    """Raised when an agent call fails."""


@dataclass
class OpenAIClient:
    """Thin wrapper over the OpenAI SDK configured for SiliconFlow."""

    api_key: str
    base_url: str
    request_timeout: float
    max_retries: int

    def __post_init__(self) -> None:
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.request_timeout,
            http_client=httpx.Client(timeout=self.request_timeout, trust_env=False),
        )

    def chat(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format=response_format,
                )
                content = response.choices[0].message.content
                if content is None:
                    raise AgentInvocationError("Received empty response from chat completion.")
                return content
            except RETRYABLE_OPENAI_ERRORS as exc:
                logger.warning("Chat completion failed on attempt %s/%s: %s", attempt, self.max_retries, exc)
                if attempt >= self.max_retries:
                    raise AgentInvocationError(f"Exceeded maximum retries for chat completion: {exc}") from exc
                time.sleep(1.0)
            except NON_RETRYABLE_OPENAI_ERRORS as exc:
                raise AgentInvocationError(f"Chat completion rejected by API: {exc}") from exc
            except OpenAIError as exc:
                raise AgentInvocationError(f"Chat completion failed: {exc}") from exc

    def embed(self, *, model: str, texts: Iterable[str]) -> List[List[float]]:
        attempt = 0
        text_list = list(texts)
        while True:
            attempt += 1
            try:
                response: CreateEmbeddingResponse = self._client.embeddings.create(model=model, input=text_list)
                return [item.embedding for item in response.data]
            except RETRYABLE_OPENAI_ERRORS as exc:
                logger.warning("Embedding request failed on attempt %s/%s: %s", attempt, self.max_retries, exc)
                if attempt >= self.max_retries:
                    raise AgentInvocationError(f"Exceeded maximum retries for embedding: {exc}") from exc
                time.sleep(1.0)
            except NON_RETRYABLE_OPENAI_ERRORS as exc:
                raise AgentInvocationError(f"Embedding request rejected by API: {exc}") from exc
            except OpenAIError as exc:
                raise AgentInvocationError(f"Embedding request failed: {exc}") from exc


def parse_agent_json(payload: str) -> Dict[str, Any]:
    """Parse agent JSON responses with leniency for stray markdown fences."""
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # Drop opening fence and potential language hint
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned, strict=False)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse agent JSON: %s\nPayload: %s", exc, cleaned)
        raise
    return _strip_keys(parsed)


def build_client(settings: Dict[str, Any]) -> OpenAIClient:
    return OpenAIClient(
        api_key=settings.get("api_key", ""),
        base_url=settings.get("base_url", ""),
        request_timeout=settings.get("request_timeout", 60.0),
        max_retries=settings.get("max_retries", 2),
    )


def _strip_keys(value: Any) -> Any:
    """Recursively strip whitespace from dictionary keys returned by agents."""
    if isinstance(value, dict):
        normalized: Dict[str, Any] = {}
        for key, item in value.items():
            new_key = key.strip() if isinstance(key, str) else key
            if isinstance(new_key, str) and not new_key:
                new_key = key
            normalized[new_key] = _strip_keys(item)
        return normalized
    if isinstance(value, list):
        return [_strip_keys(item) for item in value]
    return value
