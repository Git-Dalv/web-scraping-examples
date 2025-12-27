from scr.scrapers.scraper import scrape_jobs, get_jobs_page, create_client
from scr.plugins.llm_module.create_analysis import parse_jobs
from scr.plugins.workers_module.workers import JobScraper
from scr.plugins.save import save_results, load_jsonl
from scr.models.database import Database
from scr.models.job_saver import JobSaver
from scr.analysis.analytics import Analytics

from datetime import datetime, timezone

import argparse
import asyncio
import logging


now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def generate_analytics(db: Database, charts: list[str] = None, output_dir: str = "reports/charts",
                       seniority: str = None, work_mode: str = None):
    analytics = Analytics(db, output_dir=output_dir)

    chart_methods = {
        'skills': analytics.top_skills_chart,
        'locations': analytics.locations_chart,
        'companies': analytics.top_companies_chart,
        'seniority': analytics.seniority_chart,
        'workmode': analytics.work_mode_chart,
        'salary': analytics.salary_by_seniority_chart,
        'salary_workmode': analytics.salary_by_work_mode_chart,
        'timeline': analytics.jobs_timeline_chart,
        'benefits': analytics.top_benefits_chart,
        'requirements': analytics.top_requirements_chart,
        'heatmap': analytics.seniority_workmode_heatmap,
    }

    if charts:
        for chart_name in charts:
            if chart_name == 'skills' and seniority:
                path = analytics.top_skills_by_seniority_chart(seniority)
            elif chart_name == 'skills' and work_mode:
                path = analytics.top_skills_by_work_mode_chart(work_mode)
            elif chart_name == 'requirements' and seniority:
                path = analytics.requirements_by_seniority_chart(seniority)
            elif chart_name in chart_methods:
                path = chart_methods[chart_name]()
            else:
                print(f"Unknown chart: {chart_name}")
                print(f"Available: {', '.join(chart_methods.keys())}")
                continue
            print(f"Created: {path}")
    else:
        paths = analytics.generate_all()
        for path in paths:
            print(f"Created: {path}")

    print(analytics.summary_text())


async def run_scraper(
        db: Database,
        job_title: str,
        location: str,
        logger: logging.Logger
) -> list[dict]:
    async with create_client() as phantom:
        session = await phantom.new_session()

        try:
            jobs_page = await get_jobs_page(session, job_title, location)

            listings = await scrape_jobs(jobs_page, session)
            logger.info(f"Found: {len(listings)} jobs in listing")

            sync = db.sync_jobs_from_listing("jobs.cz", listings, job_title, location)
            logger.info(f"New: {len(sync['new'])}, Existing: {sync['existing']}, Closed: {sync['closed']}")

            if sync['new']:
                scraper = JobScraper(session=session, max_workers=3)
                raw = await scraper.scrape_all(sync['new'])
                file_path_failed = f'failed_jobs_{now}.jsonl'
                if scraper.failed_jobs:
                    save_results(scraper.failed_jobs, file_path_failed)
                    logger.warning(f"Failed jobs saved: {len(scraper.failed_jobs)}")

                return raw
            else:
                logger.info("No new jobs to scrape")
                return []

        finally:
            await session.close()


async def full_pipeline(
        db: Database,
        job_title: str,
        location: str,
        logger: logging.Logger,
        skip_analytics: bool = False
):
    raw = await run_scraper(db, job_title, location, logger)

    if raw:
        row_path = f'raw_jobs_{now}.jsonl'
        save_results(raw, row_path)
        logger.info(f"Raw jobs saved: {len(raw)}")

        parsed = await parse_jobs(raw)
        parsed_path = f'parsed_jobs_{now}.jsonl'
        save_results(parsed, parsed_path)
        logger.info(f"Parsed jobs saved: {len(parsed)}")

        saver = JobSaver(job_title=job_title, location=location, db=db, source="jobs.cz")
        stats = saver.save_batch(parsed)
        logger.info(f"Saved to DB: {stats}")

    if not skip_analytics:
        logger.info("Generating analytics...")
        generate_analytics(db)

    logger.info(f"DB Stats: {db.get_stats()}")


async def from_raw_pipeline(
        db: Database,
        raw_file: str,
        job_title: str,
        location: str,
        logger: logging.Logger,
        skip_analytics: bool = False
):
    logger.info(f"Loading raw jobs from: {raw_file}")
    raw = load_jsonl(raw_file)
    logger.info(f"Loaded: {len(raw)} jobs")

    parsed = await parse_jobs(raw)
    save_results(parsed, 'parsed_jobs.jsonl')
    logger.info(f"Parsed jobs saved: {len(parsed)}")

    saver = JobSaver(job_title=job_title, location=location, db=db, source="jobs.cz")
    stats = saver.save_batch(parsed)
    logger.info(f"Saved to DB: {stats}")

    if not skip_analytics:
        logger.info("Generating analytics...")
        generate_analytics(db)

    logger.info(f"DB Stats: {db.get_stats()}")


def from_parsed_pipeline(
        db: Database,
        parsed_file: str,
        job_title: str,
        location: str,
        logger: logging.Logger,
        skip_analytics: bool = False
):
    logger.info(f"Loading parsed jobs from: {parsed_file}")
    parsed = load_jsonl(parsed_file)
    logger.info(f"Loaded: {len(parsed)} jobs")

    saver = JobSaver(job_title=job_title, location=location, db=db, source="jobs.cz")
    stats = saver.save_batch(parsed)
    logger.info(f"Saved to DB: {stats}")

    if not skip_analytics:
        logger.info("Generating analytics...")
        generate_analytics(db)

    logger.info(f"DB Stats: {db.get_stats()}")


def parse_args():
    parser = argparse.ArgumentParser(
        description='Job Market Analyzer - Scrape, parse, and analyze job postings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              
  python main.py --job "Python" --location "Brno"
  python main.py --from-raw raw_jobs.jsonl    
  python main.py --from-parsed parsed.jsonl   
  python main.py --analytics                  
  python main.py --analytics skills salary    
  python main.py --analytics skills --seniority senior
  python main.py --analytics skills --work-mode remote
  python main.py --compare junior senior
  python main.py --stats                      
  python main.py --low-quality 0.5            
        """
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--from-raw',
        metavar='FILE',
        help='Parse and save from existing raw_jobs.jsonl'
    )

    mode.add_argument(
        '--from-parsed',
        metavar='FILE',
        help='Save from existing parsed_jobs.jsonl'
    )

    mode.add_argument(
        '--analytics',
        nargs='*',
        metavar='CHART',
        help='Only generate analytics (skills, locations, companies, seniority, workmode, salary, salary_workmode, timeline, benefits, requirements, heatmap)'
    )

    mode.add_argument(
        '--stats',
        action='store_true',
        help='Only show database statistics'
    )

    mode.add_argument(
        '--low-quality',
        type=float,
        metavar='THRESHOLD',
        help='Show jobs with parse_quality below threshold'
    )

    mode.add_argument(
        '--compare',
        nargs=2,
        metavar=('LEVEL1', 'LEVEL2'),
        help='Compare skills between two seniority levels'
    )

    parser.add_argument(
        '--job', '-j',
        default='DevOps',
        help='Job title to search (default: DevOps)'
    )

    parser.add_argument(
        '--location', '-l',
        default='Praha',
        help='Location to search (default: Praha)'
    )

    parser.add_argument(
        '--db',
        default='job_market.db',
        help='Database file path (default: job_market.db)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        default='reports/charts',
        help='Output directory for charts (default: reports/charts)'
    )

    parser.add_argument(
        '--skip-analytics',
        action='store_true',
        help='Skip analytics generation after scraping'
    )

    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output'
    )

    parser.add_argument(
        '--seniority', '-s',
        choices=['junior', 'mid', 'senior', 'lead'],
        help='Filter analytics by seniority level'
    )

    parser.add_argument(
        '--work-mode', '-w',
        choices=['remote', 'hybrid', 'on-site'],
        help='Filter analytics by work mode'
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    if args.quiet:
        logging.basicConfig(level=logging.WARNING)
    else:
        logger = setup_logging(args.debug)

    logger = logging.getLogger(__name__)

    db = Database(args.db)

    try:
        if args.stats:
            stats = db.get_stats()
            print("\nDatabase Statistics:")
            print(f"  Jobs: {stats['total_jobs']} active, {stats['archived_jobs']} archived")
            print(f"  Companies: {stats['total_companies']}")
            print(f"  Skills: {stats['total_skills']}")
            print(f"  Requirements: {stats['total_requirements']}")
            print(f"  Benefits: {stats['total_benefits']}")
            print(f"  By status: {stats['jobs_by_status']}")
            return

        if args.low_quality is not None:
            jobs = db.get_low_quality_jobs(args.low_quality)
            print(f"\nJobs with quality < {args.low_quality}: {len(jobs)}")
            for job in jobs[:20]:
                print(f"  [{job['parse_quality']:.1f}] {job['title']} - {job['source_id']}")
            if len(jobs) > 20:
                print(f"  ... and {len(jobs) - 20} more")
            return

        if args.compare:
            level1, level2 = args.compare
            analytics = Analytics(db, output_dir=args.output_dir)
            path = analytics.skills_comparison_chart(level1, level2)
            print(f"Created: {path}")
            return

        if args.analytics is not None:
            charts = args.analytics if args.analytics else None
            generate_analytics(db, charts, args.output_dir, args.seniority, args.work_mode)
            return

        if args.from_raw:
            await from_raw_pipeline(db, args.from_raw, args.job, args.location, logger, args.skip_analytics)
            return

        if args.from_parsed:
            from_parsed_pipeline(db, args.from_parsed, args.job, args.location, logger, args.skip_analytics)
            return

        await full_pipeline(
            db,
            args.job,
            args.location,
            logger,
            args.skip_analytics
        )

    finally:
        db.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise