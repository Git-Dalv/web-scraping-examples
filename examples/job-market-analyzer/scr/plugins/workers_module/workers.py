from scr.plugins.helper_functions import accept_cookies, extract_main_content
from scr.plugins.workers_module.delays import smart_delay

from datetime import datetime
from bs4 import BeautifulSoup

import asyncio
import logging
import random


logger = logging.getLogger(__name__)


class JobScraper:
    def __init__(self, session, max_workers: int = 3, delay_min: float = 1.5, delay_max: float = 4.0):
        self.session = session
        self.max_workers = max_workers
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.semaphore = asyncio.Semaphore(max_workers)
        self.lock = asyncio.Lock()

        self.processed = 0
        self.failed = 0

        self.failed_jobs: list[dict] = []

    async def _process_single_job(self, page, job: dict):
        source_id = job['source_id']
        url = job.get('url')

        try:
            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            await accept_cookies(page, self.session)

            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            text = extract_main_content(soup)

            if not text or len(text) < 200:
                logger.warning(f"Empty or short content for {source_id}")
                self.failed += 1
                async with self.lock:
                    self.failed_jobs.append({
                        'job': job,
                        'error': 'Empty or invalid content',
                    })
                return None

            self.processed += 1
            title, company, location = job.get('title'), job.get('company'), job.get('location')
            date, deadline = job.get('date'), job.get('deadline')

            a = '=' * 180
            t = '\t' * 5
            print(f'{a}')
            print(f'{t}|][| ID:{source_id} || TITLE:{title} |][|')
            print(f'|company:{company}| |location:{location}| |date:{date}| |deadline:{deadline}| |len_text: {len(text)}|')
            print(f'{a}')
            print()

            return {
                'scraped_at': datetime.now().isoformat(),
                'source_id': source_id,
                'title': title,
                'company': company,
                'location': location,
                'date': date,
                'deadline': deadline,
                'url': url,
                'raw_text': text,
            }

        except Exception as e:
            self.failed += 1
            logger.error(f"Failed to process job {source_id}: {e}")
            async with self.lock:
                self.failed_jobs.append({
                    'job': job,
                    'error': str(e),
                })
            return None

    async def _worker_semaphore(self, job: dict):
        async with self.semaphore:
            page = await self.session.new_page()
            try:
                result = await self._process_single_job(page, job)
                await smart_delay(self.delay_min, self.delay_max)
                return result
            finally:
                await page.close()

    async def scrape_all(self, jobs: list[dict], shuffle: bool = True) -> list[dict]:
        self.processed = 0
        self.failed = 0
        self.failed_jobs.clear()

        if not jobs:
            logger.info("No jobs to scrape")
            return []

        job_list = jobs.copy()
        if shuffle:
            random.shuffle(job_list)

        logger.info(f"Starting scrape of {len(job_list)} jobs with {self.max_workers} workers")

        tasks = [
            self._worker_semaphore(job)
            for job in job_list
        ]

        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            if result:
                results.append(result)

            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(tasks)} (success: {self.processed}, failed: {self.failed})")

        logger.info(
            f"Scrape complete: {self.processed} processed, {self.failed} failed"
        )

        return results

    def get_stats(self) -> dict:
        return {
            'processed': self.processed,
            'failed': self.failed,
        }