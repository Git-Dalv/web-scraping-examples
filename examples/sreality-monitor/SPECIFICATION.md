# Technical Specification: Czech Real Estate Monitor

## Project Description

**Website:** https://www.sreality.cz  
**Platform:** Sreality REST API  
**Project Type:** Real Estate Monitoring / Price Tracking  
**Market:** Czech Republic (largest real estate portal)

---

## Project Goals

1. [x] Develop a Python scraper for real estate monitoring
2. [x] Collect property listings via Sreality REST API
3. [x] Store data in SQLite database with price history tracking
4. [x] Generate interactive map with property markers (Leaflet.js)
5. [x] Provide analytics (price per m2, district comparisons, charts)
6. [x] Send Telegram notifications for new listings and price drops
7. [x] Support multiple property types and transaction types

---

## Data Collected

### Property Listing Data

| Field | Source | Description |
|-------|--------|-------------|
| `hash_id` | API | Unique property identifier |
| `name` | API | Property title |
| `price` | API | Price in CZK |
| `price_m2` | API | Price per square meter |
| `category_type_id` | API | Transaction type (sale/rent) |
| `category_main_id` | API | Property type (flat/house/land) |
| `category_sub_id` | API | Property subtype |
| `city` | API | City name |
| `citypart` | API | City district |
| `street` | API | Street name |
| `city_seo` | API | SEO-friendly city name |
| `citypart_seo` | API | SEO-friendly district name |
| `street_seo` | API | SEO-friendly street name |
| `district_id` | API | District reference |
| `region_id` | API | Region reference |
| `lat` | API | GPS latitude |
| `lon` | API | GPS longitude |
| `poi_*` | API | Points of interest distances |
| `premise_id` | API | Real estate agency ID |
| `user_id` | API | Listing owner ID |
| `has_video` | API | Video tour available |
| `has_matterport` | API | 3D tour available |
| `status` | Generated | Listing status (active/closed) |
| `first_seen_at` | Generated | First scrape timestamp |
| `last_seen_at` | Generated | Last scrape timestamp |
| `closed_at` | Generated | When listing was removed |

### Price History

| Field | Type | Description |
|-------|------|-------------|
| `hash_id` | FK | Reference to property |
| `price` | INTEGER | Price at check time |
| `price_m2` | INTEGER | Price per m2 at check time |
| `recorded_at` | DATETIME | When price was recorded |

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.9+ |
| HTTP Client | http-client-core (custom) |
| Database | SQLite |
| Map | Leaflet.js + MarkerCluster |
| Charts | matplotlib |
| Dashboard | HTML + Chart.js |
| Bot | python-telegram-bot |
| Config | YAML |

### API Endpoints Used

```
Base URL: https://www.sreality.cz/api/v1

# Filter options (regions, categories)
GET /estates/filter_page?lang=cs

# Search listings
GET /estates/search?locality_region_id={id}&category_main_cb={cat}&limit={n}&offset={o}&lang=cs

Parameters:
- locality_region_id: Region ID
- category_main_cb: 1=Flats, 2=Houses, 3=Land, 4=Commercial, 5=Other
- category_type_cb: 1=Sale, 2=Rent
- limit: Items per request (max 1000)
- offset: Pagination offset (max 10000)
- lang: Language (cs/en)
```

### Performance

- Synchronous requests with connection pooling
- Rate limiting: configurable delay between requests
- Retry logic: 3 attempts with backoff
- Batch processing: 1000 items per request
- Region + category segmentation to bypass 10k offset limit

---

## Property Types

| Type | category_main_cb | Description |
|------|------------------|-------------|
| Byty | 1 | Apartments |
| Domy | 2 | Houses |
| Pozemky | 3 | Land |
| Komercni | 4 | Commercial |
| Ostatni | 5 | Other |

### Transaction Types

| Type | category_type_cb | Description |
|------|------------------|-------------|
| Prodej | 1 | Sale |
| Pronajem | 2 | Rent |

---

## Implemented Features

### 1. Data Collection
- [x] Fetch listings via REST API
- [x] Parse property details and metadata
- [x] Extract GPS coordinates for mapping
- [x] Handle pagination with region/category segmentation
- [x] Dynamic filter loading from API
- [x] SEO URL construction for property links

### 2. Data Storage
- [x] SQLite database with normalized schema
- [x] 9 tables (estates, images, price_history, regions, districts, etc.)
- [x] Price history table for tracking changes
- [x] Deduplication by hash_id
- [x] Track listing lifecycle (active -> closed)
- [x] SEO fields for URL building

### 3. Price Tracking
- [x] Record price on each scrape
- [x] Detect price changes (increase/decrease)
- [x] Store price per m2
- [x] Price change percentage calculation

### 4. Interactive Map
- [x] Leaflet.js with OpenStreetMap tiles
- [x] Markers for each property with coordinates
- [x] Popup with property info (price, area, link)
- [x] Color coding by price per m2 range
- [x] MarkerCluster for dense areas
- [x] Filter controls (type, category, region, price, status)
- [x] Direct links to Sreality detail pages

### 5. Analytics Dashboard
- [x] General statistics (total, avg price, etc.)
- [x] Price by region table
- [x] Top districts ranking
- [x] Price distribution (text histograms)
- [x] New listings stats
- [x] Price changes log
- [x] Chart.js visualizations

### 6. Matplotlib Charts
- [x] Price per m2 by region (horizontal bar)
- [x] Price distribution histogram
- [x] Price per m2 distribution histogram
- [x] Top districts by listings (horizontal bar)
- [x] Category distribution (pie chart)
- [x] New listings timeline (line chart)
- [x] Average price by category (bar chart)

### 7. Telegram Bot
- [x] Main menu with navigation
- [x] Search by region, type, category, price
- [x] New listings today
- [x] Price drops list
- [x] Paginated property list
- [x] Property details with Sreality link
- [x] Analytics text reports
- [x] Charts as images
- [x] Subscription management
- [x] New listing alerts
- [x] Price drop notifications
- [x] Daily digest

---

## Database Schema

### Tables

| Table | Records | Description |
|-------|---------|-------------|
| `category_types` | 4 | Sale/Rent types |
| `category_main` | 5 | Property categories |
| `category_sub` | ~50 | Property subtypes |
| `regions` | 14 | Czech regions |
| `districts` | 77 | Districts |
| `premises` | ~3000 | Real estate agencies |
| `estates` | ~90000 | Property listings |
| `estate_images` | ~1.3M | Property images |
| `price_history` | Variable | Price changes |

### Indexes
- Location (city, district, region)
- Price and price_m2
- Category combinations
- GPS coordinates
- Status and timestamps

---

## Output Formats

### 1. Interactive Map (HTML)
- `web/index.html` - Full interactive map
- `web/estates.json` - Property data for map

### 2. Analytics Dashboard (HTML)
- `web/dashboard.html` - Charts and statistics
- `web/analytics.json` - Analytics data

### 3. Charts (PNG)
- `analysis/charts/price_per_m2_by_region.png`
- `analysis/charts/price_distribution.png`
- `analysis/charts/price_per_m2_distribution.png`
- `analysis/charts/top_districts.png`
- `analysis/charts/category_distribution.png`
- `analysis/charts/new_listings_timeline.png`
- `analysis/charts/price_by_category.png`

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/help` | Help message |
| `/search` | Search properties |
| `/stats` | Market statistics |
| `/subscribe` | Create subscription |
| `/my_subscriptions` | View subscriptions |

---

## Project Structure

```
sreality-monitor/
|
|-- main.py                     # CLI entry point
|-- export_map.py               # Map data export
|-- requirements.txt            # Dependencies
|-- README.md                   # Documentation
|
|-- src/
|   |-- configs/
|   |   |-- config.yaml         # HTTP client config
|   |
|   |-- database/
|   |   |-- __init__.py
|   |   |-- db.py               # Database operations
|   |   |-- estate_loader.py    # Estate data loader
|   |   |-- schema.sql          # DB schema
|   |
|   |-- scraper/
|   |   |-- __init__.py
|   |   |-- scraper.py          # API scraper
|   |
|   |-- analysis/
|   |   |-- __init__.py
|   |   |-- analytics.py        # Statistics
|   |   |-- charts.py           # Matplotlib charts
|   |
|   |-- plugins/
|   |   |-- web/
|   |   |   |-- index.html      # Interactive map
|   |   |   |-- dashboard.html  # Analytics dashboard
|   |   |   |-- estates.json    # Map data
|   |   |   |-- analytics.json  # Analytics data
|   |   |
|   |   |-- logging.py          # Logger utility
|   |
|   |-- data/
|       |-- sreality.db         # SQLite database
|
|-- telegram_bot/
|   |-- bot.py                  # Main bot
|   |-- .env                    # Bot token
|   |-- README.md               # Bot documentation
|   |-- handlers/
|   |   |-- search.py           # Search handlers
|   |   |-- analytics.py        # Analytics handlers
|   |   |-- subscriptions.py    # Subscription handlers
|   |-- services/
|   |   |-- notifications.py    # Alert service
|   |-- data/
|       |-- subscriptions.json  # User subscriptions
|
|-- docs/
|   |-- README.md               # Main documentation
|   |-- API.md                  # API documentation
|   |-- DATABASE.md             # Schema documentation
|   |-- BOT.md                  # Telegram bot guide
|   |-- ANALYTICS.md            # Analytics guide
|   |-- images/                 # Screenshots
|
|-- logs/                       # Log files
```

---

## Dependencies

```
requests>=2.31.0
pyyaml>=6.0
python-dotenv>=1.0.0
python-telegram-bot>=20.0
matplotlib>=3.7.0
```

---

## Results

| Metric | Value |
|--------|-------|
| Total estates scraped | ~90,000 |
| Total images | ~1,300,000 |
| Regions covered | 14 |
| Districts covered | 77 |
| Real estate agencies | ~3,000 |
| Scraping time | ~45 minutes |
| Database size | ~150 MB |

---

## Legal & Ethical Notes

- Sreality API is unofficial - rate limits respected
- For educational/portfolio use
- Configurable delay between requests
- No personal data stored beyond public listings
