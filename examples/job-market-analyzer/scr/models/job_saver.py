import logging
from typing import Optional
from scr.models.database import Database

logger = logging.getLogger(__name__)


class JobSaver:
    def __init__(self, job_title: str, location: str, db: Database, source: str = "jobs.cz"):
        self.job_title = job_title
        self.location = location
        self.db = db
        self.source = source
        self.saved_count = 0
        self.skipped_count = 0

    def save_job(self, raw_job: dict, parsed: dict) -> Optional[int]:
        source_id = str(raw_job.get("source_id") or raw_job.get("id"))

        # Check if already exists
        if self.db.job_exists(self.source, source_id):
            self.skipped_count += 1
            logger.debug(f"Job {source_id} already exists, skipping")
            return None

        general = parsed.get("General", {})
        salary = parsed.get("Salary", {})
        salary_est = parsed.get("Salary_Estimate", {})

        # Get or create company
        company_name = general.get("Company")
        if not company_name or company_name == "null" or company_name == "Not specified":
            company_name = raw_job.get("company")
        company_id = self.db.get_or_create_company(company_name) if company_name else None

        # Get or create skills
        technologies = parsed.get("Technologies", [])
        skill_ids = [self.db.get_or_create_skill(t) for t in technologies]

        # Get or create requirements
        requirements = parsed.get("Requirements", [])
        requirement_ids = [self.db.get_or_create_requirement(r) for r in requirements]

        # Get or create benefits
        benefits = parsed.get("Benefits", [])
        benefit_ids = [self.db.get_or_create_benefit(b) for b in benefits]

        location = general.get("Location")
        if not location or location in ("null", "None", "Not specified", "Unknown"):
            location = raw_job.get("location")
        print(f'Lens: benefits {len(benefits)} | technologies {len(technologies)} | requirements {len(requirements)} ')

        quality = self._calculate_quality(parsed, company_name)

        # Create job
        job_id = self.db.create_job(
            source=self.source,
            source_id=source_id,
            url=raw_job.get("url"),
            title=general.get("JobTitle") or raw_job.get("title"),
            company_id=company_id,
            location=location,
            job_type=general.get("JobType"),
            work_mode=general.get("WorkMode"),
            seniority=general.get("Seniority"),
            experience_min=general.get("ExperienceYearsMin"),
            employment_language=general.get("EmploymentLanguage"),
            salary_min=salary.get("Min"),
            salary_max=salary.get("Max"),
            salary_currency=salary.get("Currency"),
            salary_period=salary.get("Period"),
            salary_estimate=salary_est.get("Avg"),
            salary_confidence=salary_est.get("Confidence"),
            description=parsed.get("Description", []),
            parse_quality=quality,
            search_job_title=self.job_title,
            search_location=self.location,
            deadline=raw_job.get("deadline") if raw_job.get("deadline") else None,
            scraped_at=raw_job.get("scraped_at"),
            skill_ids=skill_ids,
            requirement_ids=requirement_ids,
            benefit_ids=benefit_ids,
        )

        self.saved_count += 1
        logger.debug(f"Saved job {source_id} with ID {job_id}")
        return job_id

    def save_batch(self, jobs: list[dict]) -> dict:
        self.saved_count = 0
        self.skipped_count = 0

        for job in jobs:
            parsed = job.get("parsed", {})
            if parsed:
                self.save_job(job, parsed)

        logger.info(f"Batch complete: {self.saved_count} saved, {self.skipped_count} skipped")

        return {
            "saved": self.saved_count,
            "skipped": self.skipped_count,
            "total": len(jobs),
        }

    def _calculate_quality(self, parsed: dict, company_name: str) -> float:
        quality = 0.0

        if parsed.get("Technologies"):
            quality += 0.4
        if parsed.get("Requirements"):
            quality += 0.3
        if parsed.get("Benefits"):
            quality += 0.2
        if company_name and company_name not in ("null", "Not specified", "Unknown"):
            quality += 0.1

        return quality


def save_parsed_jobs(parsed_jobs: list[dict], db_path: str = "job_market.db", source: str = "jobs.cz") -> dict:
    db = Database(db_path)
    saver = JobSaver(db, source)
    stats = saver.save_batch(parsed_jobs)
    db.close()
    return stats
