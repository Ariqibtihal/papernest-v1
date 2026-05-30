from __future__ import annotations

import asyncio
import json
from typing import Any

from google import genai
from google.genai import types as genai_types
from loguru import logger

from app.config import get_settings


class AIService:
    """
    Singleton wrapper around the Google Gemini API for semantic paper reranking.

    If no GOOGLE_API_KEY is configured the service is a no-op and returns
    zero scores for every paper, so the rest of the ranking pipeline still works.
    """

    _instance: AIService | None = None
    _client: genai.Client | None = None
    _model: str = "gemini-1.5-flash"

    def __new__(cls) -> AIService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            if settings.google_api_key:
                cls._client = genai.Client(api_key=settings.google_api_key)
                logger.info(f"AIService initialised with model={cls._model}")
            else:
                logger.debug("AIService: no GOOGLE_API_KEY — semantic reranking disabled")
        return cls._instance

    async def rerank_papers(self, query: str, papers: list[Any]) -> list[float]:
        """
        Return a list of semantic relevance scores (0.0–1.0) for each paper.
        Falls back to all-zeros if the API is unavailable or not configured.
        """
        if not self._client or not papers:
            return [0.0] * len(papers)

        papers_data = [
            {
                "id": i,
                "title": p.title,
                "abstract": (p.abstract[:200] + "...") if p.abstract else "No abstract",
            }
            for i, p in enumerate(papers)
        ]

        prompt = (
            f'Rate the semantic relevance of each research paper to the query: "{query}"\n'
            'Return a JSON object with a list of scores between 0 and 1, where 1 is highly relevant.\n'
            'Format: {"scores": [0.9, 0.2, 0.5, ...]}\n'
            "Return ONLY the JSON.\n\n"
            f"Papers:\n{json.dumps(papers_data)}"
        )

        try:
            # google-genai is synchronous — run in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self._model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            text = response.text.strip()

            # Strip markdown fences if the model wraps the JSON anyway
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            scores: list[float] = data.get("scores", [])

            if len(scores) != len(papers):
                logger.warning(
                    f"Gemini returned {len(scores)} scores for {len(papers)} papers — padding"
                )
                scores = (scores + [0.0] * len(papers))[: len(papers)]

            return [float(s) for s in scores]

        except Exception:
            logger.exception("Semantic reranking failed")
            return [0.0] * len(papers)
