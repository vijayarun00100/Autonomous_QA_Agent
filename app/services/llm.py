from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from langchain_groq import ChatGroq

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set. Please configure it in the environment.")
        self.model_name = settings.groq_model
        self.client = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=self.model_name,
            temperature=0.2,
            max_tokens=None,
        )
        logger.info("Initialized Groq Chat model %s", self.model_name)

    def get_model(self) -> ChatGroq:
        return self.client


@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService()
