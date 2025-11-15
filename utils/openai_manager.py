from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional
import json
import time

from openai import OpenAI
from config.settings import AppConfig
from utils.logger import AppLogger


class OpenAIManager:
    """Prompt-agnostic wrapper around OpenAI Responses and Embeddings APIs."""

    def __init__(self, cfg: AppConfig, logger: Optional[AppLogger] = None) -> None:
        self.cfg = cfg
        self.logger = logger or AppLogger(cfg.log_file_path)
        self.client = OpenAI(api_key=cfg.openai_api_key)

    # ---------------- Public API ----------------

    def structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        *,
        model: Optional[str] = None,
        max_output_tokens: int = 1500,
        retries: int = 3,
        timeout_s: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call Chat Completions with JSON Schema response_format and parse JSON.

        Uses OpenAI Python SDK v2.x `chat.completions.create` which supports
        `response_format={"type":"json_schema", "json_schema": {...}}`.
        """
        mdl = model or self.cfg.openai_model
        tmo = float(timeout_s if timeout_s is not None else self.cfg.request_timeout_seconds)

        last_err: Optional[Exception] = None
        for attempt in range(1, int(retries) + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=mdl,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "structured_output",
                            "schema": json_schema,
                            "strict": True,
                        },
                    },
                    max_tokens=max_output_tokens,
                    timeout=tmo,
                )
                content = resp.choices[0].message.content if resp.choices else "{}"
                return json.loads(content or "{}")
            except Exception as e:
                last_err = e
                self.logger.log_kv("OPENAI_JSON_RETRY", attempt=attempt, error=str(e))
                time.sleep(min(2 ** attempt, 8))
        self.logger.log_kv("OPENAI_JSON_FAIL", error=str(last_err) if last_err else "unknown")
        if last_err:
            raise last_err
        raise RuntimeError("structured_json failed")

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
        max_output_tokens: int = 1000,
        temperature: float = 0.0,
        retries: int = 3,
        timeout_s: Optional[float] = None,
    ) -> str:
        """Plain text completion via Responses API."""
        mdl = model or self.cfg.openai_model
        tmo = float(timeout_s if timeout_s is not None else self.cfg.request_timeout_seconds)

        last_err: Optional[Exception] = None
        for attempt in range(1, int(retries) + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=mdl,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_output_tokens,
                    timeout=tmo,
                )
                return resp.choices[0].message.content if resp.choices else ""
            except Exception as e:
                last_err = e
                self.logger.log_kv("OPENAI_CHAT_RETRY", attempt=attempt, error=str(e))
                time.sleep(min(2 ** attempt, 8))
        self.logger.log_kv("OPENAI_CHAT_FAIL", error=str(last_err) if last_err else "unknown")
        if last_err:
            raise last_err
        raise RuntimeError("chat_text failed")

    def embed_texts(
        self,
        texts: Iterable[str],
        *,
        model: Optional[str] = None,
        retries: int = 3,
        timeout_s: Optional[float] = None,
    ) -> List[List[float]]:
        """Batch-embed a list/iterable of strings. Returns a list of vectors."""
        mdl = model or self.cfg.openai_embedding_model
        tmo = float(timeout_s if timeout_s is not None else self.cfg.request_timeout_seconds)

        items = list(texts)
        last_err: Optional[Exception] = None
        for attempt in range(1, int(retries) + 1):
            try:
                resp = self.client.embeddings.create(
                    model=mdl,
                    input=items,
                    timeout=tmo,
                )
                return [d.embedding for d in getattr(resp, "data", [])]
            except Exception as e:
                last_err = e
                self.logger.log_kv("OPENAI_EMBED_RETRY", attempt=attempt, error=str(e))
                time.sleep(min(2 ** attempt, 8))
        self.logger.log_kv("OPENAI_EMBED_FAIL", error=str(last_err) if last_err else "unknown")
        if last_err:
            raise last_err
        raise RuntimeError("embed_texts failed")
