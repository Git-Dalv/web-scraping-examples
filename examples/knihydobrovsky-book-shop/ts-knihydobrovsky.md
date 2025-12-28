# 📋 Technical Specification: Knihy Dobrovský Book Shop Scraper

---

## 🎯 Project Description

**Website:** https://www.knihydobrovsky.cz  
**Platform:** Custom Czech E-commerce  
**Project Type:** Web Scraping / Price Monitoring  
**Client:** Czech bookstore owner (competitor price analysis)

---

## 📌 Project Goals

1. Develop a **synchronous Python scraper** for book price monitoring
2. Collect bestseller catalog data from competitor website
3. Extract embedded JSON data from `data-productinfo` attributes
4. Handle invalid JSON format (unquoted string values)
5. Generate analytical reports (CSV, JSON) with discount analysis
6. Provide Top-10 reports for business decisions

---

## 📊 Data to Collect

### From Product Listing (Embedded JSON + HTML):

| Field | Source | Example |
|-------|--------|---------|
| `id` | data-productinfo JSON | "803031659" |
| `title` | data-productinfo JSON (name) | "Manželství" |
| `author` | data-productinfo JSON (brand) | "Patrik Hartl" |
| `original_price` | HTML (.price-common) | 449 Kč |
| `price` | HTML (.price strong) | 379 Kč |
| `discount_percent` | Calculated | 15.59% |
| `rating` | data-productinfo JSON | "4.5" |
| `availability` | data-productinfo JSON (available) | "Skladem" |
| `category` | data-productinfo JSON | "Knihy/Beletrie/..." |
| `labels` | data-productinfo JSON | "Bestsellery" |
| `url` | Constructed from ID | Full product URL |
| `sale` | Calculated (price < original) | true/false |

### Data Source Challenge:

**Problem:** `data-productinfo` contains invalid JSON:
```json
{"id": 803031659, "name": Manželství, "price": 499.00}
```
String values lack quotes.

**Solution:** Regex-based JSON repair before parsing.

---

## 🔧 Technical Requirements

### Technology Stack:
- **Python 3.9+**
- **requests** + **BeautifulSoup4** for scraping
- **pandas** for data analysis
- **http-client-core** (custom library) for HTTP handling
- **re** for JSON repair

### Performance Requirements:
- **Rate limiting:** 0.5 requests/second
- **Delay between requests:** 2 sec with ±1 sec jitter
- **Retry on errors:** 3 attempts with exponential backoff
- **Circuit breaker:** 5 failures threshold

---

## 📂 Categories to Parse

| Category | URL Path | Description |
|----------|----------|-------------|
| Bestsellery | /bestsellery | Top selling books |
| Novinky | /novinky | New arrivals |
| Knihy v akci | /knihy-v-akci | Discounted books |

---

## 📋 Functional Requirements

### 1. Data Collection
- [x] Fetch category pages with pagination
- [x] Extract `data-productinfo` from each product item
- [x] Repair invalid JSON (add missing quotes)
- [x] Parse prices from HTML (JSON prices unreliable)
- [x] Handle Czech characters (UTF-8)

### 2. Data Processing
- [x] Calculate discount percentage
- [x] Identify sale products (price < original_price)
- [x] Remove duplicates by product ID
- [x] Sort by various criteria

### 3. Report Generation
- [x] Export all products to JSON
- [x] Export sale products to CSV
- [x] Generate Top-10 discounts report
- [x] Generate Top-10 rated products report

---

## 📤 Output Data Format

### CSV Structure:
```csv
title,author,price,original_price,discount_percent,availability,rating,category,sale,url
"Manželství","Patrik Hartl",379.0,449.0,15.59,"Skladem","4.5","Knihy/Beletrie/...",true,"https://..."
```

### JSON Structure:
```json
{
  "id": "803031659",
  "title": "Manželství",
  "author": "Patrik Hartl",
  "original_price": 449.0,
  "price": 379.0,
  "discount_percent": 15.59,
  "rating": "4.5",
  "availability": "Skladem",
  "category": "Knihy/Beletrie/Česká a slovenská beletrie",
  "labels": "Bestsellery",
  "url": "https://www.knihydobrovsky.cz/kniha/manzelstvi-803031659",
  "sale": true
}
```

---

## ✅ Acceptance Criteria

1. Scraper successfully collects data from all target categories
2. Pagination is handled correctly
3. Invalid JSON is repaired and parsed without errors
4. Prices are extracted from HTML (not JSON) for accuracy
5. Czech characters display correctly in output files
6. Top-10 reports generated for business analysis
7. Code is documented and maintainable
8. README with usage instructions provided

---

## 💰 Project Value

**Estimated freelance price:** $200-350  
**Timeline:** 3-5 days  
**Complexity:** Entry-level (good portfolio starter)

### Skills Demonstrated:
- HTTP requests with custom client
- HTML parsing with BeautifulSoup4
- JSON repair and parsing
- Data analysis with pandas
- UTF-8 encoding handling
- Professional project structure

---

## 🔗 Dependencies

- [http-client-core](https://github.com/Git-Dalv/http-client-core) - Custom HTTP client with rate limiting
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- pandas >= 2.0.0
- pyyaml >= 6.0
