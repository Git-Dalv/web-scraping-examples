# Web Scraping Portfolio

**Python Developer | Web Scraping & Data Extraction Specialist**

This portfolio showcases my web scraping expertise across multiple domains and complexity levels — from simple HTTP-based scrapers to advanced browser automation with LLM integration.

---

## Core Technologies

| Category | Technologies |
|----------|-------------|
| **HTTP Clients** | requests, httpx, aiohttp, custom http-client-core |
| **Parsing** | BeautifulSoup4, lxml, selectolax |
| **Browser Automation** | Playwright, Selenium, phantom-persona (anti-detection) |
| **Async** | asyncio, concurrent workers, queue-based patterns |
| **Data Storage** | SQLite, pandas, JSON/CSV export |
| **AI/LLM** | OpenAI GPT-4o-mini for unstructured data extraction |
| **Visualization** | Matplotlib, Leaflet.js, interactive dashboards |

---

## Projects

### 1. Crypto News & Price Alert System

**Problem Solved:** Cryptocurrency investors need to correlate price movements with news events to make informed decisions. Manual monitoring of multiple sources is time-consuming and inefficient.

**Solution:** Automated system that monitors top cryptocurrencies, detects significant price movements (configurable threshold), fetches related news articles, analyzes sentiment, and generates comprehensive reports.

| Metric | Value |
|--------|-------|
| **Complexity** | Entry → Mid |
| **APIs** | CoinGecko (prices), CoinDesk (news) |
| **Output** | Markdown digest + JSON reports |
| **Key Feature** | Sentiment analysis (positive/negative/neutral) |

**Tech Stack:** Python, asyncio, custom http-client-core, pandas

📂 **[View Project →](examples/crypto-news-price-alert/)** | 📄 **[README](examples/crypto-news-price-alert/README.md)**

---

### 2. Euroelectronics E-commerce Scraper (Shopify)

**Problem Solved:** E-commerce businesses need competitor price data and product catalog information for market analysis, but Shopify stores have rate limiting and pagination challenges.

**Solution:** Production-ready async scraper with queue-based worker pattern, intelligent duplicate detection, and comprehensive product data extraction including prices, descriptions, specifications, and images.

| Metric | Value |
|--------|-------|
| **Complexity** | Mid |
| **Products** | ~700+ items across 8 categories |
| **Pattern** | Producer-consumer with asyncio Queue |
| **Key Feature** | Circuit breaker + exponential backoff |

**Tech Stack:** Python, asyncio, BeautifulSoup4, custom http-client-core, pandas

📂 **[View Project →](examples/e-commerce-euroelectronics-shopify/)** | 📄 **[README](examples/e-commerce-euroelectronics-shopify/README.md)**

---

### 3. Knihy Dobrovský Book Shop Scraper

**Problem Solved:** A bookstore owner needs competitor price analysis to stay competitive. The target site stores product data in malformed JSON (unquoted string values) embedded in HTML attributes.

**Solution:** Scraper with custom JSON repair logic that fixes invalid JSON before parsing, extracts accurate prices from HTML (not unreliable JSON), and generates Top-10 reports for business decisions.

| Metric | Value |
|--------|-------|
| **Complexity** | Entry-level |
| **Challenge** | Invalid JSON repair with regex |
| **Output** | CSV + JSON with discount analysis |
| **Key Feature** | Top-10 discounts & ratings reports |

**Tech Stack:** Python, requests, BeautifulSoup4, pandas, custom http-client-core

📂 **[View Project →](examples/knihydobrovsky-book-shop/)** | 📄 **[README](examples/knihydobrovsky-book-shop/README.md)**

---

### 4. Job Market Analyzer

**Problem Solved:** Job aggregators like jobs.cz redirect 30-40% of listings to external company websites, each with unique HTML structure. Writing individual parsers is impractical. Additionally, job postings contain unstructured text with embedded salary, skills, and requirements data.

**Solution:** Browser automation with anti-detection (phantom-persona) combined with LLM-based extraction (GPT-4o-mini) that works with ANY HTML structure. The system extracts structured data from unstructured job descriptions and normalizes it into a queryable database.

| Metric | Value |
|--------|-------|
| **Complexity** | Advanced |
| **Challenge** | External redirects + unstructured data |
| **Innovation** | LLM extraction (~$0.001-0.002/job) |
| **Features** | CLI + Telegram bot + Analytics charts |

**Tech Stack:** Python, Playwright, phantom-persona, OpenAI API, SQLite, Matplotlib, pyTelegramBotAPI

📂 **[View Project →](examples/job-market-analyzer/)** | 📄 **[README](examples/job-market-analyzer/README.md)** 

---

### 5. Sreality Real Estate Monitor

**Problem Solved:** Real estate market analysis requires comprehensive data across all regions, but the Sreality API has a 10,000 listing limit per query, and the total market has ~90,000 listings.

**Solution:** Discovered and reverse-engineered internal JSON API. Implemented segmentation strategy (by region → by category) to bypass pagination limits. Built interactive map with clustering, price history tracking, and Telegram bot with subscription alerts.

| Metric | Value |
|--------|-------|
| **Complexity** | Advanced |
| **Data Volume** | ~90,000 properties, ~1.3M images |
| **Regions** | 14 regions, 77 districts |
| **Database** | ~150 MB normalized SQLite |

**Tech Stack:** Python, requests, SQLite, Leaflet.js, Telegram Bot API, Matplotlib

📂 **[View Project →](examples/sreality-monitor/)** | 📄 **[README](examples/sreality-monitor/README.md)** 

---

##  Skills Progression

```
Entry Level          Mid Level              Advanced
     │                   │                     │
     ▼                   ▼                     ▼
┌─────────┐      ┌──────────────┐      ┌────────────────┐
│ HTTP    │  →   │ Async HTTP   │  →   │ Browser Auto   │
│ requests│      │ aiohttp      │      │ Playwright     │
└─────────┘      └──────────────┘      └────────────────┘
     │                   │                     │
     ▼                   ▼                     ▼
┌─────────┐      ┌──────────────┐      ┌────────────────┐
│ HTML    │  →   │ JSON APIs    │  →   │ LLM Extraction │
│ Parsing │      │ Discovery    │      │ GPT-4o-mini    │
└─────────┘      └──────────────┘      └────────────────┘
     │                   │                     │
     ▼                   ▼                     ▼
┌─────────┐      ┌──────────────┐      ┌────────────────┐
│ CSV     │  →   │ SQLite +     │  →   │ Full Stack     │
│ Export  │      │ Analytics    │      │ Web + Bot      │
└─────────┘      └──────────────┘      └────────────────┘
```

---

## Custom Libraries

### [http-client-core](https://github.com/Git-Dalv/http-client-core)
Production-ready HTTP client with:
- Automatic retry with exponential backoff
- Rate limiting (token bucket algorithm)
- Circuit breaker pattern
- YAML configuration

### [phantom-persona](https://github.com/Git-Dalv/phantom-persona)
Playwright-based anti-detection library with:
- Randomized fingerprints
- Human-like delays
- Proxy rotation support

---

## Contact

**Available for freelance projects:**
- E-commerce price monitoring
- Lead generation & contact extraction
- Market research & competitor analysis
- Real estate & job market data
- Custom API integrations

---

## License

All projects are MIT licensed for educational and portfolio purposes.
