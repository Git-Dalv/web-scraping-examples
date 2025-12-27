from scr.models import sql
from scr.models.enums import JobStatus, CloseReason

from datetime import datetime, date
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

import sqlite3
import json
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "job_market.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._init_db()

    @contextmanager
    def _get_cursor(self):
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def _init_db(self):
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Database initialized: {self.db_path}")

    def _create_tables(self):
        with self._get_cursor() as cursor:
            for table in sql.ALL_TABLES:
                cursor.execute(table)
            for index in sql.CREATE_INDEXES:
                cursor.execute(index)

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        return text.strip().lower()

    # ==================== Companies ====================

    def get_or_create_company(self, name: str) -> Optional[int]:
        if not name:
            return None

        normalized = self._normalize(name)
        today = date.today().isoformat()

        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_COMPANY_BY_NAME, (normalized,))
            row = cursor.fetchone()

            if row:
                cursor.execute(sql.UPDATE_COMPANY_COUNT, (today, row["id"]))
                return row["id"]

            cursor.execute(sql.INSERT_COMPANY, (name, normalized, today, today))
            return cursor.lastrowid

    def get_company(self, company_id: int) -> Optional[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_COMPANY_BY_ID, (company_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_top_companies(self, limit: int = 20) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_TOP_COMPANIES, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Skills ====================

    def get_or_create_skill(self, name: str, category: str = None) -> Optional[int]:
        if not name:
            return None

        normalized = self._normalize(name)
        today = date.today().isoformat()

        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_SKILL_BY_NAME, (normalized,))
            row = cursor.fetchone()

            if row:
                cursor.execute(sql.UPDATE_SKILL_COUNT, (today, row["id"]))
                return row["id"]

            cursor.execute(sql.INSERT_SKILL, (name, normalized, category, today, today))
            return cursor.lastrowid

    def get_top_skills(self, limit: int = 20) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_TOP_SKILLS, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_skills_by_category(self, category: str) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_SKILLS_BY_CATEGORY, (category,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Requirements ====================

    def get_or_create_requirement(self, text: str) -> Optional[int]:
        if not text:
            return None

        normalized = self._normalize(text)

        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_REQUIREMENT_BY_TEXT, (normalized,))
            row = cursor.fetchone()

            if row:
                cursor.execute(sql.UPDATE_REQUIREMENT_COUNT, (row["id"],))
                return row["id"]

            cursor.execute(sql.INSERT_REQUIREMENT, (text, normalized))
            return cursor.lastrowid

    def get_top_requirements(self, limit: int = 20) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_TOP_REQUIREMENTS, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Benefits ====================

    def get_or_create_benefit(self, text: str) -> Optional[int]:
        if not text:
            return None

        normalized = self._normalize(text)

        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_BENEFIT_BY_TEXT, (normalized,))
            row = cursor.fetchone()

            if row:
                cursor.execute(sql.UPDATE_BENEFIT_COUNT, (row["id"],))
                return row["id"]

            cursor.execute(sql.INSERT_BENEFIT, (text, normalized))
            return cursor.lastrowid

    def get_top_benefits(self, limit: int = 20) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_TOP_BENEFITS, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Jobs ====================

    def job_exists(self, source: str, source_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_JOB_EXISTS, (source, source_id))
            return cursor.fetchone() is not None

    def create_job(
            self,
            source: str,
            source_id: str,
            url: str,
            title: str,
            company_id: int,
            location: str = None,
            job_type: str = None,
            work_mode: str = None,
            seniority: str = None,
            experience_min: int = None,
            employment_language: str = None,
            salary_min: float = None,
            salary_max: float = None,
            salary_currency: str = None,
            salary_period: str = None,
            salary_estimate: float = None,
            salary_confidence: float = None,
            description: list[str] = None,
            parse_quality: float = 0.0,
            search_job_title: str = None,
            search_location: str = None,
            deadline: str = None,
            scraped_at: str = None,
            skill_ids: list[int] = None,
            requirement_ids: list[int] = None,
            benefit_ids: list[int] = None,
    ) -> int:
        now = datetime.now().isoformat()
        description_json = json.dumps(description) if description else None

        with self._get_cursor() as cursor:
            cursor.execute(sql.INSERT_JOB, (
                source, source_id, url, title, company_id, location,
                job_type, work_mode, seniority, experience_min, employment_language,
                salary_min, salary_max, salary_currency, salary_period,
                salary_estimate, salary_confidence,
                description_json, parse_quality, search_job_title, search_location,
                JobStatus.NEW.value, deadline, scraped_at, now
            ))
            job_id = cursor.lastrowid

            # Link skills
            if skill_ids:
                for skill_id in skill_ids:
                    if skill_id:
                        cursor.execute(sql.INSERT_JOB_SKILL, (job_id, skill_id))

            # Link requirements
            if requirement_ids:
                for req_id in requirement_ids:
                    if req_id:
                        cursor.execute(sql.INSERT_JOB_REQUIREMENT, (job_id, req_id))

            # Link benefits
            if benefit_ids:
                for ben_id in benefit_ids:
                    if ben_id:
                        cursor.execute(sql.INSERT_JOB_BENEFIT, (job_id, ben_id))

            return job_id

    def get_job(self, job_id: int) -> Optional[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_JOB_BY_ID, (job_id,))
            row = cursor.fetchone()
            if not row:
                return None

            job = dict(row)
            job["description"] = json.loads(job["description"]) if job["description"] else []

            # Get skills
            cursor.execute(sql.SELECT_JOB_SKILLS, (job_id,))
            job["skills"] = [dict(r) for r in cursor.fetchall()]

            # Get requirements
            cursor.execute(sql.SELECT_JOB_REQUIREMENTS, (job_id,))
            job["requirements"] = [dict(r) for r in cursor.fetchall()]

            # Get benefits
            cursor.execute(sql.SELECT_JOB_BENEFITS, (job_id,))
            job["benefits"] = [dict(r) for r in cursor.fetchall()]

            return job

    def get_jobs_by_status(self, status: str, limit: int = 100) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_JOBS_BY_STATUS, (status, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_jobs(self, limit: int = 20) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_RECENT_JOBS, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_job_status(self, job_id: int, status: str):
        with self._get_cursor() as cursor:
            cursor.execute(sql.UPDATE_JOB_STATUS, (status, datetime.now().isoformat(), job_id))

    # ==================== Archive ====================

    def archive_job(self, job_id: int, close_reason: str):
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_JOB_BY_ID, (job_id,))
            job = cursor.fetchone()
            if not job:
                return

            job = dict(job)
            now = datetime.now()

            # Calculate lifetime
            scraped_at = datetime.fromisoformat(job["scraped_at"]) if job["scraped_at"] else now
            lifetime_days = (now - scraped_at).days

            # Insert into archive
            cursor.execute(sql.INSERT_JOB_ARCHIVE, (
                job["id"], job["source"], job["source_id"], job["url"],
                job["title"], job["company_id"], job["location"],
                job["job_type"], job["work_mode"], job["seniority"],
                job["experience_min"], job["employment_language"],
                job["salary_min"], job["salary_max"], job["salary_currency"], job["salary_period"],
                job["salary_estimate"], job["salary_confidence"],
                job["description"], job["status"], job["deadline"],
                job["scraped_at"], job["parsed_at"], job["last_checked"],
                now.isoformat(), close_reason, lifetime_days
            ))

            # Delete from jobs
            cursor.execute(sql.DELETE_JOB_SKILLS, (job_id,))
            cursor.execute(sql.DELETE_JOB_REQUIREMENTS, (job_id,))
            cursor.execute(sql.DELETE_JOB_BENEFITS, (job_id,))
            cursor.execute(sql.DELETE_JOB, (job_id,))

            logger.info(f"Archived job {job_id}: {close_reason}")

    def expire_jobs_by_deadline(self) -> int:
        today = date.today().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_EXPIRED_JOBS, (today,))
            expired = cursor.fetchall()

            for row in expired:
                self.archive_job(row["id"], CloseReason.EXPIRED.value)

            logger.info(f"Expired {len(expired)} jobs")
            return len(expired)

    # ==================== Statistics ====================

    def get_stats(self) -> dict:
        with self._get_cursor() as cursor:
            stats = {}

            cursor.execute(sql.COUNT_JOBS)
            stats["total_jobs"] = cursor.fetchone()["count"]

            cursor.execute(sql.COUNT_ARCHIVED)
            stats["archived_jobs"] = cursor.fetchone()["count"]

            cursor.execute(sql.COUNT_COMPANIES)
            stats["total_companies"] = cursor.fetchone()["count"]

            cursor.execute(sql.COUNT_SKILLS)
            stats["total_skills"] = cursor.fetchone()["count"]

            cursor.execute(sql.COUNT_REQUIREMENTS)
            stats["total_requirements"] = cursor.fetchone()["count"]

            cursor.execute(sql.COUNT_BENEFITS)
            stats["total_benefits"] = cursor.fetchone()["count"]

            cursor.execute(sql.COUNT_JOBS_BY_STATUS)
            stats["jobs_by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}

            return stats

    def sync_jobs_from_listing(self, source: str, found_jobs: list[dict],
                               job_title: str, location: str) -> dict:
        found_ids = {str(job.get('source_id') or job.get('id')) for job in found_jobs}

        stats = {'new': [], 'existing': 0, 'closed': 0}

        with self._get_cursor() as cursor:
            cursor.execute(sql.CHECK_JOBS_BY_SEARCH, (source, job_title, location))
            db_jobs = {row['source_id']: row['id'] for row in cursor.fetchall()}
            db_ids = set(db_jobs.keys())

            new_ids = found_ids - db_ids
            stats['new'] = [j for j in found_jobs if str(j.get('source_id') or j.get('id')) in new_ids]

            existing_ids = found_ids & db_ids
            now = datetime.now().isoformat()
            for source_id in existing_ids:
                cursor.execute(sql.UPDATE_IT, (now, source, source_id))
            stats['existing'] = len(existing_ids)

            closed_ids = db_ids - found_ids
            for source_id in closed_ids:
                job_id = db_jobs[source_id]
                self.archive_job(job_id, CloseReason.CLOSED.value)
            stats['closed'] = len(closed_ids)

        return stats

    def get_low_quality_jobs(self, threshold: float = 0.5) -> list[dict]:
        with self._get_cursor() as cursor:
            cursor.execute(sql.SELECT_LOW_QUALITY_JOBS, (threshold,))
            return [dict(row) for row in cursor.fetchall()]


    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
