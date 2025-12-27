import argparse
import logging
import time
from pathlib import Path
from datetime import datetime


def setup_logging(enable_logging: bool, log_level: str = 'INFO'):
    """Configure logging to file and console."""
    if not enable_logging:
        logging.disable(logging.CRITICAL)
        return None

    project_root = Path(__file__).parent
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f'scraper_{timestamp}.log'

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clear existing handlers and configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(numeric_level)

    formatter = logging.Formatter(log_format, date_format)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    logging.info(f"Logging initialized. Log file: {log_file}")

    return log_file


def main():
    parser = argparse.ArgumentParser(
        description='Euroelectronics web scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Scrape all collections
  python main.py --mode categories            # Use predefined categories
  python main.py --log                        # Enable logging
  python main.py --mode categories --log --log-level DEBUG
  python main.py --log --verbose              # Enable HTTP client logging
        """
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['collections', 'categories'],
        default='collections',
        help='Scraping mode: collections (all) or categories (predefined)'
    )

    parser.add_argument(
        '--log',
        action='store_true',
        help='Enable logging to file'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Application logging level (default: INFO)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose HTTP client logging (includes requests/responses)'
    )

    args = parser.parse_args()
    use_categories = args.mode == 'categories'

    # Setup logging BEFORE importing modules with loggers
    log_file = setup_logging(args.log, args.log_level)

    # Import AFTER logging is configured
    from scr.scrapers.scraper import get_result
    from scr.analysis.pandas_analyse import analyse_it, save_to_json

    if args.verbose:
        logging.getLogger('httpx').setLevel(logging.DEBUG)
        logging.getLogger('httpcore').setLevel(logging.DEBUG)
        logging.getLogger('http_client').setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)

    print(f"{'='*50}")
    print(f"Mode: {args.mode}")
    print(f"Logging: {'Enabled' if args.log else 'Disabled'}")
    if args.log:
        print(f"Log Level: {args.log_level}")
        print(f"Verbose HTTP: {'Yes' if args.verbose else 'No'}")
        print(f"Log File: {log_file}")
    print(f"{'='*50}\n")

    try:
        logger.info(f"Starting scraper in {args.mode} mode")
        data = get_result(categories=use_categories)
        logger.info(f"Scraping completed. Total products: {len(data)}")

        logger.info("Starting data analysis")
        save_to_json(data)
        analyse_it(data)
        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    start = time.perf_counter()
    main()
    print(f"\nFinished in {time.perf_counter() - start:.2f}s")