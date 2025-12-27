# Euroelectronics E-commerce Scraper

A production-ready asynchronous web scraper for extracting product data from euroelectronics.eu (Shopify platform). Built with Python 3.9+ using async/await patterns and a custom HTTP client library with advanced rate limiting, circuit breaker pattern, and intelligent retry logic.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Files](#output-files)
- [Technical Details](#technical-details)
- [HTTP Client Core Library](#http-client-core-library)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)
- [Legal and Ethical Considerations](#legal-and-ethical-considerations)
- [License](#license)

---

## Overview

This scraper is designed to collect complete product catalog data from Euroelectronics, a European electronics retailer running on the Shopify platform. The scraper handles pagination, rate limiting, and fault tolerance automatically, producing structured output in both JSON and CSV formats.

Key metrics:
- Target: ~700-5000 products depending on mode
- Average runtime: 15-45 minutes for full catalog
- Memory usage: < 200MB
- Success rate: 99%+ with proper configuration

---

## Features

### Core Functionality
- Asynchronous scraping with asyncio and queue-based worker pattern
- Complete catalog extraction including all product details
- Automatic pagination handling for collections and product listings
- Duplicate detection and filtering across collections
- Sale product identification with discount calculation
- EU compliance data extraction (lowest price in 30 days)

### Reliability
- Intelligent retry logic with exponential backoff and jitter
- Circuit breaker pattern for fault tolerance
- Rate limiting with configurable delays
- Automatic recovery from transient errors
- Comprehensive error logging without stopping execution

### Data Export
- JSON export with complete nested data structure
- CSV export for spreadsheet analysis
- Separate sale products report sorted by discount
- Timestamped output files for version tracking
- UTF-8 encoding with proper handling of special characters

### HTTP Client Features (via http-client-core)
- Connection pooling for efficient resource usage
- User-Agent rotation to avoid detection
- Proxy support via configuration
- Request/response logging for debugging
- Configurable timeouts (connect, read, total)

---

## Project Structure

```
e-commerce-euroelectronics-shopify/
│
├── main.py                          # Application entry point with CLI
├── requirements.txt                 # Python dependencies
├── README.md                        # This documentation file
│
├── configs/
│   ├── euroelectronics_config.yaml  # Production HTTP client configuration
│   └── config_dev.yaml              # Development configuration (optional)
│
├── scr/
│   ├── __init__.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── pandas_analyse.py        # Data processing, normalization, export
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── scraper.py               # Core async scraping logic
│   │
│   └── plugins/
│       ├── __init__.py
│       ├── cleaner.py               # Price parsing and cleaning utilities
│       └── description_cleaner.py   # HTML description parsing
│
├── logs/                            # Log files directory (auto-created)
│   └── scraper_YYYYMMDD_HHMMSS.log
│
└── reports/                         # Output files directory (auto-created)
    ├── all_YYYYMMDD_HHMMSS.json     # Complete dataset with all fields
    ├── products_YYYYMMDD_HHMMSS.csv # All products in flat format
    └── sale_YYYYMMDD_HHMMSS.csv     # Sale products sorted by discount
```

---

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (for installing http-client-core)
- Virtual environment (recommended)
- Internet connection with stable bandwidth

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/e-commerce-euroelectronics-shopify.git
cd e-commerce-euroelectronics-shopify
```

### 2. Create Virtual Environment

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install HTTP Client Core Library

This project requires the custom async HTTP client library:

```bash
pip install git+https://github.com/Git-Dalv/http-client-core.git
```

For additional features:
```bash
# Async support (httpx)
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[async]

# YAML configuration support
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[yaml]

# All optional dependencies
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[all]
```

### 5. Verify Installation

```bash
python -c "from http_client import AsyncHTTPClient; print('Installation successful')"
```

---

## Configuration

### HTTP Client Configuration

The scraper configuration is stored in `configs/euroelectronics_config.yaml`. This file controls all HTTP client behavior including rate limiting, retries, and connection management.

```yaml
http_client:
  base_url: "https://euroelectronics.eu"

  # Timeouts (seconds)
  timeout:
    connect: 10          # Time to establish connection
    read: 30             # Time to receive response
    total: 60            # Total request timeout

  # Retry strategy for failed requests
  retry:
    max_attempts: 3           # Total attempts including initial
    backoff_base: 2.0         # Initial delay between retries
    backoff_factor: 2.0       # Multiplier (2s -> 4s -> 8s)
    backoff_max: 60.0         # Maximum delay cap
    backoff_jitter: true      # Randomize delays to avoid patterns
    respect_retry_after: true # Honor Retry-After header
    retry_after_max: 120      # Maximum Retry-After to respect

  # Connection pool settings
  pool:
    connections: 10           # Keep-alive connections
    maxsize: 15               # Maximum concurrent connections
    max_redirects: 5          # Follow redirects limit

  # Security settings
  security:
    verify_ssl: true
    allow_redirects: true
    max_response_size: 10485760   # 10MB limit

  # Circuit breaker for fault tolerance
  circuit_breaker:
    enabled: true
    failure_threshold: 5      # Failures before opening circuit
    recovery_timeout: 30.0    # Seconds before retry
    half_open_max_calls: 2    # Test requests when recovering

  # HTTP headers (browser mimicry)
  headers:
    User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    Accept-Language: "en-GB,en;q=0.9"
    Accept-Encoding: "identity"    # Disabled compression for reliability
    Connection: "keep-alive"

  # Logging configuration
  logging:
    level: "INFO"
    format: "text"
    enable_console: true
    log_request_body: false
    log_response_body: false
```

### Configuration Parameters Explained

#### Timeout Settings
- `connect`: Maximum time to establish TCP connection
- `read`: Maximum time to receive the complete response
- `total`: Overall timeout including all retries

#### Retry Settings
- `max_attempts`: How many times to retry failed requests
- `backoff_base`: Starting delay between retries
- `backoff_factor`: Multiplier applied after each retry
- `backoff_jitter`: Adds randomness to prevent synchronized retries

#### Circuit Breaker
The circuit breaker prevents cascading failures by temporarily stopping requests after multiple failures:
- CLOSED: Normal operation, requests proceed
- OPEN: Too many failures, requests fail immediately
- HALF-OPEN: Testing if service recovered

#### Pool Settings
Connection pooling improves performance by reusing TCP connections:
- `connections`: Persistent connections to maintain
- `maxsize`: Upper limit on concurrent connections

---

## Usage

### Command-Line Interface

```bash
python main.py [OPTIONS]
```

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--mode` | choice | collections | Scraping mode: `collections` or `categories` |
| `--log` | flag | False | Enable logging to file |
| `--log-level` | choice | INFO | Log verbosity: DEBUG, INFO, WARNING, ERROR |
| `--verbose` | flag | False | Enable verbose HTTP client logging |

### Scraping Modes

#### Collections Mode (Default)
Discovers and scrapes all collections from the website:
```bash
python main.py --mode collections --log
```

This mode:
- Fetches the collections index page
- Extracts all collection URLs (approximately 194 collections)
- Filters out aggregate collections (/all-, /total)
- Scrapes all products from each collection
- Handles duplicates across collections

#### Categories Mode
Uses predefined category list for faster, targeted scraping:
```bash
python main.py --mode categories --log
```

Predefined categories:
- /collections/electronics (~150 products)
- /collections/audio (~80 products)
- /collections/office-supplies (~100 products)
- /collections/car-accessories (~90 products)
- /collections/house (~120 products)
- /collections/sale (~700 products)
- /collections/sport (~50 products)
- /collections/toys-games (~60 products)

### Usage Examples

Standard production run with logging:
```bash
python main.py --log
```

Debug mode with verbose HTTP logging:
```bash
python main.py --log --log-level DEBUG --verbose
```

Quick test with predefined categories:
```bash
python main.py --mode categories --log
```

Minimal output (no log files):
```bash
python main.py --mode categories
```

---

## Output Files

All output files are saved in the `reports/` directory with timestamps to prevent overwriting.

### Complete Dataset (JSON)

**File:** `reports/all_YYYYMMDD_HHMMSS.json`

Contains all product data with nested structures:

```json
[
  {
    "sale": true,
    "product_name": "Audiocore AC9900 Bluetooth Car Stereo MP3 USB AUX",
    "vendor": "Audiocore",
    "in_stock": true,
    "price_regular": 81.14,
    "price_sale": 60.81,
    "discount_percent": 25.06,
    "currency": "EUR",
    "category": "audio",
    "product_url": "https://euroelectronics.eu/collections/audio/products/audiocore-ac9900",
    "SKU": "AC9900",
    "lowest_price_30d": 60.81,
    "image_url": [
      "https://euroelectronics.eu/cdn/shop/products/image1.jpg",
      "https://euroelectronics.eu/cdn/shop/products/image2.jpg"
    ],
    "description": "High-quality Bluetooth car stereo with MP3 playback...",
    "specifications": {
      "Bluetooth Version": "5.0",
      "Output Power": "4x50W",
      "Display": "LCD"
    }
  }
]
```

### All Products (CSV)

**File:** `reports/products_YYYYMMDD_HHMMSS.csv`

Flat structure suitable for spreadsheet analysis:

| Column | Description |
|--------|-------------|
| SKU | Product stock keeping unit |
| product_name | Full product title |
| vendor | Manufacturer/brand name |
| price_regular | Original price in EUR |
| price_sale | Discounted price (if applicable) |
| discount_percent | Calculated discount percentage |
| in_stock | Availability status |
| category | Collection category |
| product_url | Full URL to product page |

### Sale Products (CSV)

**File:** `reports/sale_YYYYMMDD_HHMMSS.csv`

Contains only products with active discounts, sorted by discount percentage (highest first):

| Column | Description |
|--------|-------------|
| SKU | Product identifier |
| product_name | Full product title |
| vendor | Brand name |
| price_regular | Original price |
| price_sale | Current sale price |
| discount_percent | Discount percentage |
| category | Product category |
| product_url | Link to product |

### Log Files

**File:** `logs/scraper_YYYYMMDD_HHMMSS.log`

Contains detailed execution log:

```
2024-12-18 15:30:00 - __main__ - INFO - Logging initialized
2024-12-18 15:30:01 - scr.scrapers.scraper - INFO - Scraper started
2024-12-18 15:30:02 - scr.scrapers.scraper - INFO - Fetching collections from: /collections
2024-12-18 15:30:05 - scr.scrapers.scraper - INFO - Found 194 collections
2024-12-18 15:30:06 - scr.scrapers.scraper - INFO - Fetching products from: /collections/electronics
2024-12-18 15:30:15 - scr.scrapers.scraper - INFO - Found 156 products across 7 pages
2024-12-18 15:30:16 - scr.scrapers.scraper - INFO - Queued 156 from /collections/electronics
...
2024-12-18 15:42:30 - __main__ - INFO - Scraping completed. Total products: 5386
2024-12-18 15:42:31 - __main__ - INFO - Analysis completed successfully
```

---

## Technical Details

### Scraping Architecture

The scraper uses an asynchronous queue-based architecture with worker pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                        main()                                │
├─────────────────────────────────────────────────────────────┤
│  1. get_collections()      Fetch collection URLs            │
│           │                                                  │
│           v                                                  │
│  2. For each collection:                                     │
│     ├── get_all_products()  Fetch product URLs              │
│     └── Queue URLs          Add to asyncio.Queue            │
│           │                                                  │
│           v                                                  │
│  3. Workers (x3)           Parallel product scrapers        │
│     └── scrape_product_page()  Extract product data         │
│           │                                                  │
│           v                                                  │
│  4. Results collection     Aggregate all products           │
│           │                                                  │
│           v                                                  │
│  5. pandas_analyse()       Process and export data          │
└─────────────────────────────────────────────────────────────┘
```

### Concurrency Model

The scraper uses a shared semaphore to limit concurrent requests:

```python
sem = asyncio.Semaphore(3)  # Maximum 3 concurrent requests

# Collection fetching uses semaphore
async with sem:
    products = await get_all_products(client, collection_url)

# Workers also use same semaphore
async with sem:
    product = await scrape_product_page(client, url)
```

This ensures the total request rate stays within acceptable limits regardless of which operation is executing.

### Queue-Based Worker Pattern

Products are scraped using a producer-consumer pattern:

1. **Producer**: Main loop fetches collections and adds product URLs to queue
2. **Consumers**: Worker tasks pull URLs from queue and scrape products
3. **Synchronization**: `queue.join()` waits for all items to be processed

Benefits:
- Products start scraping before all collections are fetched
- Memory efficient (no need to store all URLs at once)
- Graceful handling of variable collection sizes

### Duplicate Detection

Products can appear in multiple collections. The scraper uses a global set with async lock:

```python
SEEN_NAMES = set()
SEEN_LOCK = asyncio.Lock()

async with SEEN_LOCK:
    if name not in SEEN_NAMES:
        _products_href.append(url)
        SEEN_NAMES.add(name)
```

### Data Extraction

Each product page yields the following data points:

| Field | Source | Notes |
|-------|--------|-------|
| product_name | h1 element | Full product title |
| vendor | Vendor link | Manufacturer name |
| price_regular | .money span | Original price |
| price_sale | .money span | Discounted price (if exists) |
| discount_percent | Calculated | (regular - sale) / regular * 100 |
| in_stock | data-product-inventory | "In stock" or "Low stock" |
| SKU | .sku span | Stock keeping unit |
| lowest_price_30d | .bpi-price | EU compliance field |
| image_url | image-element tags | All product images |
| description | .rte div | Cleaned HTML content |
| specifications | Parsed from description | Key-value pairs |
| category | URL path | Extracted from collection URL |

### Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| HTTP 429 (Rate Limit) | Exponential backoff, respect Retry-After |
| HTTP 5xx (Server Error) | Retry with backoff |
| Network Timeout | Retry up to max_attempts |
| Parse Error | Log warning, skip product, continue |
| Circuit Open | Wait for recovery_timeout, then retry |

---

## HTTP Client Core Library

This project is built on top of [http-client-core](https://github.com/Git-Dalv/http-client-core), a custom async HTTP client library designed for web scraping workloads.

### Key Features

| Feature | Description |
|---------|-------------|
| Smart Retry | Exponential backoff with jitter, Retry-After support |
| Circuit Breaker | Fault tolerance with automatic recovery |
| Connection Pooling | Efficient TCP connection reuse |
| Async Support | Full async/await API via httpx |
| Configuration | YAML/JSON config with hot reload |
| Proxy Support | Proxy rotation with health tracking |

### Basic Usage

```python
from http_client import AsyncHTTPClient
from http_client.core.env_config import ConfigFileLoader

# Load configuration from YAML
config = ConfigFileLoader.from_yaml("config.yaml")

# Create async client with configuration
async with AsyncHTTPClient(config=config) as client:
    response = await client.get("/products")
    print(response.text)
```

### Available HTTP Methods

```python
async with AsyncHTTPClient(base_url="https://example.com") as client:
    # GET request
    response = await client.get("/path", params={"page": 1})
    
    # POST with JSON
    response = await client.post("/api", json={"key": "value"})
    
    # POST with form data
    response = await client.post("/login", data={"user": "name"})
    
    # Other methods
    response = await client.put("/resource/1", json={...})
    response = await client.patch("/resource/1", json={...})
    response = await client.delete("/resource/1")
    response = await client.head("/resource")
```

### Installation Options

```bash
# Basic installation
pip install git+https://github.com/Git-Dalv/http-client-core.git

# With async support
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[async]

# With YAML config support
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[yaml]

# All features
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[all]
```

### Repository

GitHub: [https://github.com/Git-Dalv/http-client-core](https://github.com/Git-Dalv/http-client-core)

---

## Troubleshooting

### Issue: HTTP 429 (Too Many Requests)

**Symptoms:** Logs show "Rate limit exceeded" or "Max retries exceeded"

**Solutions:**

1. Increase delays in configuration:
```yaml
retry:
  backoff_base: 3.0      # Increase from 2.0
  backoff_max: 120.0     # Increase from 60.0
```

2. Reduce concurrency in `scraper.py`:
```python
sem = asyncio.Semaphore(2)  # Reduce from 3
```

3. Increase sleep times:
```python
await asyncio.sleep(3.0)  # Increase from 1.5
```

### Issue: Circuit Breaker Opens

**Symptoms:** Logs show "Circuit breaker is OPEN"

**Solutions:**

1. Increase failure threshold:
```yaml
circuit_breaker:
  failure_threshold: 10    # Increase from 5
  recovery_timeout: 60.0   # Increase from 30.0
```

2. Wait and retry later (server may be overloaded)

### Issue: Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'http_client'`

**Solution:**
```bash
pip install git+https://github.com/Git-Dalv/http-client-core.git#egg=http-client-core[all]
```

### Issue: Encoding Errors in Output

**Symptoms:** Strange characters in CSV/JSON files

**Solution:** Ensure proper encoding in file operations:
```python
with open(filename, 'w', encoding='utf-8', newline='') as f:
    # Write data
```

### Issue: Gzip/Brotli Decoding Errors

**Symptoms:** Response text shows binary garbage

**Solution:** Disable compression in headers:
```yaml
headers:
  Accept-Encoding: "identity"  # Instead of "gzip, deflate, br"
```

### Issue: Empty Results

**Symptoms:** Scraper completes but reports 0 products

**Possible causes:**
1. Website structure changed - check selectors
2. IP blocked - try different network/proxy
3. Circuit breaker stuck open - restart scraper

---

## Performance Optimization

### Conservative Settings (Recommended)

For reliable scraping without rate limiting:

```yaml
retry:
  max_attempts: 4
  backoff_base: 3.0
  backoff_max: 120.0

circuit_breaker:
  failure_threshold: 10
  recovery_timeout: 60.0
```

```python
sem = asyncio.Semaphore(2)
await asyncio.sleep(2.0)  # Between requests
```

Expected performance: ~1 request per 3 seconds, full catalog in 45-60 minutes

### Aggressive Settings (Use with Caution)

For faster scraping (risk of rate limiting):

```yaml
retry:
  max_attempts: 2
  backoff_base: 1.0
  backoff_max: 30.0

circuit_breaker:
  failure_threshold: 5
  recovery_timeout: 30.0
```

```python
sem = asyncio.Semaphore(5)
await asyncio.sleep(0.5)  # Between requests
```

Expected performance: ~3-5 requests per second, full catalog in 15-20 minutes

Warning: Aggressive settings may result in IP bans or incomplete data.

---

## Legal and Ethical Considerations

- This scraper is provided for educational purposes
- Review and respect the target website's robots.txt file
- Review and comply with the website's Terms of Service
- Implement reasonable rate limiting to avoid server overload
- Do not run multiple instances simultaneously against the same target
- Use collected data responsibly and in compliance with applicable laws
- Consider reaching out to the website for official API access
- GDPR and other privacy regulations may apply to collected data

---

## License

This project is provided as-is for educational purposes. See LICENSE file for details.

---

## Acknowledgments

- Built with [http-client-core](https://github.com/Git-Dalv/http-client-core)
- Powered by [asyncio](https://docs.python.org/3/library/asyncio.html), [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/), and [pandas](https://pandas.pydata.org/)
- Target website: [Euroelectronics.eu](https://euroelectronics.eu)
