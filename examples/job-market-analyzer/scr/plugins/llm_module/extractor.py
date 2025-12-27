from scr.plugins.llm_module.models import JobPosting
from scr.plugins.llm_module.prompts import SYSTEM_PROMPT, FALLBACK_PROMPT

from typing import Optional
from openai import AsyncOpenAI

import json
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _validate_required_fields(parsed: JobPosting) -> bool:
    general = parsed.General

    if not general.JobTitle:
        return False
    if not general.Company:
        return False

    if not parsed.Technologies and not parsed.Requirements:
        return False

    return True


class JobExtractor:
    def __init__(
            self,
            api_key: str,
            model: str = "gpt-4o-mini",
            temperature: float = 0,
            max_tokens: int = 3500,
            max_workers: int = 5,
            max_retries: int = 2
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.semaphore = asyncio.Semaphore(max_workers)
        self.max_retries = max_retries

    async def _call_llm(self, prompt: str, text: str) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text.strip()},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    async def _extract_fallback(self, job_text: str) -> JobPosting:
        logger.info("Using fallback extraction...")

        data = await self._call_llm(FALLBACK_PROMPT, job_text)
        return JobPosting.model_validate(data)

    async def extract(self, job_text: str) -> JobPosting:
        async with self.semaphore:
            if not job_text or not job_text.strip():
                raise ValueError("Job text cannot be empty")

            last_error = None

            for attempt in range(self.max_retries + 1):
                try:
                    data = await self._call_llm(SYSTEM_PROMPT, job_text)
                    validated = JobPosting.model_validate(data)

                    if _validate_required_fields(validated):
                        return validated

                    logger.warning(
                        f"Missing required fields, attempt {attempt + 1}/{self.max_retries + 1}. "
                        f"JobTitle={validated.General.JobTitle}, "
                        f"Company={validated.General.Company}, "
                        f"Tech={len(validated.Technologies)}"
                    )
                    last_error = ValueError("Missing required fields")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed: {e}")
                    last_error = ValueError(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Extraction failed: {e}")
                    last_error = e

            try:
                return await self._extract_fallback(job_text)
            except Exception as e:
                logger.error(f"Fallback extraction failed: {e}")
                raise last_error

    async def extract_batch(self, job_texts: list[str], raise_on_error: bool = False) -> list[Optional[JobPosting]]:

        async def extract_with_index(index: int, text: str):
            try:
                result = await self.extract(text)
                return index, result
            except Exception as e:
                logger.error(f"Failed job {index}: {e}")
                if raise_on_error:
                    raise
                return index, None

        tasks = [extract_with_index(i, text) for i, text in enumerate(job_texts)]
        completed = await asyncio.gather(*tasks)
        completed.sort(key=lambda x: x[0])

        results = [result for _, result in completed]
        success = sum(1 for r in results if r)
        logger.info(f"Batch complete: {success}/{len(job_texts)} extracted")

        return results