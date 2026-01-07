from src.plugins.logging import create_logger
from src.database.estate_loader import EstateLoader
from src.database.db import Database

from http_client import HTTPClient
from http_client.core.env_config import ConfigFileLoader

from pathlib import Path
import time

logger = create_logger(__name__)

MAX_OFFSET = 10000


def _client() -> HTTPClient:
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "configs" / "config.yaml"
    config = ConfigFileLoader.from_yaml(config_path)
    client = HTTPClient(config=config)
    return client


def get_filters():
    url = '/api/v1/estates/filter_page'
    params = {'lang': 'en'}
    with _client() as client:
        response = client.get(url, params=params)
        data = response.json()
    return data


def get_regions(db: Database) -> list[int]:
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM regions ORDER BY id")
    return [row[0] for row in cursor.fetchall()]


def get_categories_main(db: Database) -> list[int]:
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM category_main ORDER BY id")
    return [row[0] for row in cursor.fetchall()]


def _fetch_segment(client, loader, search_url, base_params, segment_name, step, delay):
    offset = 0
    fetched = 0
    failed = []
    
    params = {**base_params, "limit": 1, "lang": "cs"}
    response = client.get(search_url, params=params)
    data = response.json()
    total = data["pagination"]["total"]
    
    if total == 0:
        return fetched, failed
    
    logger.info(f"{segment_name}: {total} items")
    
    if total > MAX_OFFSET:
        logger.warning(f"{segment_name} exceeds {MAX_OFFSET}, will be truncated")
    
    while offset < total and offset < MAX_OFFSET:
        params = {**base_params, "limit": step, "offset": offset, "lang": "cs"}
        
        try:
            response = client.get(search_url, params=params)
            data = response.json()
            results = data.get("results", [])
            
            if results:
                loader.load_batch(results)
                fetched += len(results)
            
            logger.info(f"{segment_name}: {offset + len(results)}/{min(total, MAX_OFFSET)}")
            
        except Exception as e:
            failed.append({"segment": segment_name, "offset": offset, "error": str(e)})
            logger.error(f"{segment_name} offset {offset}: {e}")
        
        offset += step
        time.sleep(delay)
    
    return fetched, failed


def get_all_data(db: Database, step: int = 1000, delay: float = 0.5):
    loader = EstateLoader(db)
    search_url = '/api/v1/estates/search'
    
    regions = get_regions(db)
    categories_main = get_categories_main(db)
    
    logger.info(f"Loaded {len(regions)} regions, {len(categories_main)} categories from DB")
    
    failed_requests = []
    total_fetched = 0
    
    with _client() as client:
        for region_id in regions:
            params = {"locality_region_id": region_id, "limit": 1, "lang": "cs"}
            response = client.get(search_url, params=params)
            data = response.json()
            region_total = data["pagination"]["total"]
            
            if region_total == 0:
                continue
            
            if region_total <= MAX_OFFSET:
                base_params = {"locality_region_id": region_id}
                fetched, failed = _fetch_segment(
                    client, loader, search_url, base_params,
                    f"Region {region_id}", step, delay
                )
                total_fetched += fetched
                failed_requests.extend(failed)
            else:
                logger.info(f"Region {region_id}: {region_total} items (splitting by category)")
                
                for cat_main in categories_main:
                    base_params = {
                        "locality_region_id": region_id,
                        "category_main_cb": cat_main
                    }
                    fetched, failed = _fetch_segment(
                        client, loader, search_url, base_params,
                        f"Region {region_id} / Cat {cat_main}", step, delay
                    )
                    total_fetched += fetched
                    failed_requests.extend(failed)
    
    stats = loader.get_stats()
    closed = loader.mark_closed_estates()
    
    logger.info("=" * 50)
    logger.info("Scraping complete!")
    logger.info(f"Total processed: {total_fetched}")
    logger.info(f"New estates: {stats['new_estates']}")
    logger.info(f"Price changes: {stats['price_changes']}")
    logger.info(f"Closed estates: {closed}")
    logger.info(f"Images: {stats['images']}")
    logger.info(f"Premises: {stats['premises']}")
    logger.info(f"Failed requests: {len(failed_requests)}")
    logger.info("=" * 50)
    
    return {
        "stats": stats,
        "closed": closed,
        "failed": failed_requests
    }