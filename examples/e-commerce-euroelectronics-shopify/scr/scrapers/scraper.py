import asyncio
import logging
from http_client import AsyncHTTPClient
from http_client.core.env_config import ConfigFileLoader
from pathlib import Path
from bs4 import BeautifulSoup
from scr.plugins.cleaner import price_cleaner, m_cleaner, clean_text
from scr.plugins.description_cleaner import parse_product_description
from urllib.parse import urljoin
import re


logger = logging.getLogger(__name__)
SEEN_NAMES = set()
SEEN_LOCK = asyncio.Lock()
EXCLUDE_PATTERNS = ['/all-', '/total']


def _get_config():
    """"Returns the configuration."""
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "configs" / "euroelectronics_config.yaml"
    return ConfigFileLoader.from_yaml(config_path)


async def scrape_product_page(client: AsyncHTTPClient, url_path: str) -> dict:
    """Parses a product page."""
    logger.debug(f"Scraping product: {url_path}")

    page = await client.get(url_path)
    page_soup = BeautifulSoup(page.text, "html.parser")
    part_main = page_soup.find('main')

    _sale = False
    _product_url = urljoin(client.base_url, url_path)
    match = re.search(r'collections/([^/]+)', url_path)
    _category = match.group(1) if match else "unknown"

    if not part_main:
        logger.error(f"Main element not found on {url_path}")
        raise Exception(f"Main element not found on {url_path}")

    part_text = part_main.find('div', id=re.compile('sub$'))
    description = part_text.find('div', class_='rte')
    if description:
        _description, _specifications = parse_product_description(str(description))
    else:
        _description, _specifications = "", {}

    part_info = part_main.find('div', class_=re.compile('product$'))
    if not part_info:
        logger.error(f"Page info not found on {url_path}")
        raise Exception(f"Page info not found on {url_path}")

    seen = set()
    _img_urls = []
    img_path = part_info.find('div', attrs={'data-product-images': True})
    if img_path:
        imgs = img_path.find_all('image-element')
        for img_url in imgs:
            base_url = img_url.find('img')['src']
            if base_url.split('?')[0] not in seen:
                seen.add(base_url.split('?')[0])
                if base_url.startswith('//'):
                    base_url = 'https:' + base_url
                _img_urls.append(base_url)

    part_product = part_info.find('div', class_=re.compile('meta$'))
    part_header = part_product.find('div', class_=re.compile('header$'))

    _vendor = clean_text(part_header.find('div', class_=re.compile('vendor$')).find("a", href=True).text.strip())
    _title = clean_text(part_header.find('h1', class_=True).text.strip())

    part_data_product = part_product.find('div', attrs={'data-product-blocks': True})
    if not part_data_product:
        logger.error(f"Product not found on {url_path}")
        raise Exception(f"Product not found on {url_path}")

    _sku = part_data_product.find('span', class_=re.compile('sku$')).text.strip()
    prices = part_data_product.find_all('span', class_='money')
    if not prices:
        logger.error(f"Product not found on {url_path}")
        raise Exception(f"Product not found on {url_path}")
    price_texts = list(p.get_text(strip=True) for p in prices)
    price = list(set(map(price_cleaner, price_texts)))
    _price = {
        'price_regular': max(price),
        'price_sale': min(price),
        'discount_percent': round(((max(price) - min(price)) / max(price) * 100), 2),
        'ISO': 'EUR'
    }
    if max(price) > min(price):
        _sale = True
    data_product_inventory = part_data_product.find('span', attrs={'data-product-inventory': True}).text.strip()
    _in_stock = 'In stock' in data_product_inventory or 'Low stock' in data_product_inventory

    low_price_elem = part_data_product.find('span', class_="bpi-price")
    _low_price = m_cleaner(low_price_elem.text.strip()) if low_price_elem else 0.0

    logger.debug(f"Successfully scraped: {_sku} - {_title}")

    return {
        'sale': _sale,
        'product_name': _title,
        'vendor': _vendor,
        'in_stock': _in_stock,
        'price': _price,
        'category': _category,
        'product_url': _product_url,
        'details': {
            'SKU': _sku,
            'lowest_price_30d': _low_price,
            'image_url': _img_urls,
            'description': _description,
            'specifications': _specifications,
        }
    }


async def get_collections(client: AsyncHTTPClient, url: str, categories: bool) -> list:
    """Fetches all collections."""
    logger.info(f"Fetching collections from: {url}")
    if categories:
        logger.info("Using predefined categories")
        urls = [
            '/collections/electronics',
            '/collections/audio',
            '/collections/office-supplies',
            '/collections/car-accessories',
            '/collections/house',
            '/collections/sale',
            '/collections/sport',
            '/collections/toys-games'
        ]
    else:
        _url_collection = []
        while True:
            page = await client.get(url)
            bs_page = BeautifulSoup(page.text, "html.parser")
            part_main = bs_page.find('main', id='MainContent')
            if not part_main:
                logger.error(f"Main element not found on {url}")
                raise Exception(f"Main element not found on {url}")

            part_collection = part_main.find('div', class_='grid grid--uniform')
            if not part_collection:
                logger.error(f"Collection not found on {url}")
                raise Exception(f"Collection not found on {url}")

            part_collections = part_collection.find_all('div', class_=re.compile(r'one-quarter'))
            for collection in part_collections:
                temp = collection.find('a')
                if temp and temp['href'] not in _url_collection:
                    _url_collection.append(temp['href'])

            part_pag = part_main.find('div', class_='pagination')
            if not part_pag:
                break
            part_next = part_pag.find('span', class_='next')
            if not part_next:
                break
            url = part_next.find('a')['href']
            await asyncio.sleep(1.3)
        urls = [c for c in _url_collection
                    if not any(pattern in c.lower() for pattern in EXCLUDE_PATTERNS)]
        logger.info(f"Found {len(urls)} collections")
    return urls


async def get_all_products(client: AsyncHTTPClient, url: str) -> list:
    """Fetches all products from a collection."""
    logger.info(f"Fetching products from: {url}")
    _products_href = []
    page_count = 0

    while True:
        page_count += 1
        page = await client.get(url)
        bs_page = BeautifulSoup(page.text, "html.parser")

        part_main = bs_page.find('main', id='MainContent')
        if not part_main:
            logger.error(f"Main element not found on {url}")
            raise Exception(f"Main element not found on {url}")

        part_data = part_main.find('div', attrs={'data-scroll-to': True})
        if not part_data:
            logger.error(f"Product not found on {url}")
            raise Exception(f"Product not found on {url}")

        part_products = part_data.find('div', class_='grid grid--uniform')
        if not part_products:
            logger.error(f"Product not found on {url}")
            raise Exception(f"Product not found on {url}")

        products = part_products.find_all('div', attrs={'data-product-id': True})

        for product in products:
            name_elem = product.find('div', class_=re.compile(r'grid-product__title'))
            name = name_elem.get_text(strip=True).lower()

            async with SEEN_LOCK:
                if name not in SEEN_NAMES:
                    _products_href.append(product.find('a')['href'])
                    SEEN_NAMES.add(name)

        part_pag = part_main.find('div', class_='pagination')
        if not part_pag:
            break

        part_next = part_pag.find('span', class_='next')
        if not part_next:
            break

        url = part_next.find('a')['href']
        await asyncio.sleep(1.5)

    logger.info(f"Found {len(_products_href)} products across {page_count} pages")
    return _products_href


async def scrape_products_batch(client: AsyncHTTPClient, urls: list, semaphore: asyncio.Semaphore) -> list:
    """Parses products in parallel with rate limiting."""
    logger.info(f"Starting batch scraping of {len(urls)} products")

    async def fetch_one(url):
        async with semaphore:
            try:
                result = await scrape_product_page(client, url)
                await asyncio.sleep(1.3)
                return result

            except Exception as e:
                logger.warning(f"Error scraping {url}: {e}")
                return None

    tasks = [fetch_one(url) for url in urls]
    results = await asyncio.gather(*tasks)
    successful = [r for r in results if r is not None]

    logger.info(f"Batch scraping completed: {len(successful)}/{len(urls)} successful")
    return successful


async def main(categories: bool = False):
    """
    Main scraper entry point.
    """
    config = _get_config()
    sem = asyncio.Semaphore(3)
    sem_prod = asyncio.Semaphore(4)

    product_queue = asyncio.Queue()
    results = []

    async with AsyncHTTPClient(config=config) as client:
        logger.info("Fetching all collections...")
        collections = await get_collections(client, '/collections', categories)

        async def product_worker():
            while True:
                url = await product_queue.get()
                if url is None:
                    break
                async with sem:
                    try:
                        product = await scrape_product_page(client, url)
                        results.append(product)
                    except Exception as e:
                        logger.warning(f"Error: {url} - {e}")
                    await asyncio.sleep(1.3)
                product_queue.task_done()

        workers = [asyncio.create_task(product_worker()) for _ in range(3)]

        for collection_url in collections:
            async with sem_prod:
                try:
                    product_urls = await get_all_products(client, collection_url)
                    for url in product_urls:
                        await product_queue.put(url)
                    logger.info(f"Queued {len(product_urls)} from {collection_url}")
                except Exception as e:
                    logger.warning(f"Skip {collection_url}: {e}")
                await asyncio.sleep(1.3)

        await product_queue.join()

        for _ in workers:
            await product_queue.put(None)
        await asyncio.gather(*workers)

        return results


def get_result(categories: bool = False):
    return asyncio.run(main(categories))