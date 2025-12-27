# 📋 Technical Specification: European Electronics E-commerce Parser

---

## 🎯 Project Description

**Website:** https://euroelectronics.eu  
**Platform:** Shopify  
**Project Type:** Web Scraping / Data Extraction  

---

## 📌 Project Goals

1. Develop an **asynchronous Python parser** for product data collection
2. Collect complete product catalog (~700+ items) across all categories
3. Implement pagination and category handling
4. Track promotional products (SALE section)
5. Save data in structured format (CSV/JSON)
6. Ensure capability for regular data updates

---

## 📊 Data to Collect

### From Catalog (Product List):

| Field | Description | Example |
|-------|-------------|---------|
| `product_name` | Product name | "AUDIOCORE AC9900 Bluetooth Car Stereo" |
| `brand` | Brand | "Audiocore" |
| `price_regular` | Regular price | €81.14 |
| `price_sale` | Sale price | €60.81 |
| `discount_percent` | Discount percentage | 25% |
| `product_url` | Product link | /products/autoradio-met-scherm... |
| `image_url` | Image URL | //euroelectronics.eu/cdn/shop/... |
| `category` | Category | "Audio Technology" |
| `in_stock` | Availability | true/false |

### From Product Page (Details):

| Field | Description |
|-------|-------------|
| `sku` | Product SKU |
| `full_description` | Full description |
| `specifications` | Technical specifications |
| `images_all` | All product images |
| `lowest_price_30d` | Lowest price in 30 days (EU requirement) |

---

## 🔧 Technical Requirements

### Technology Stack:
- **Python 3.9+**
- **Async HTTP Client** (httpx / aiohttp / custom)
- **BeautifulSoup4** or **selectolax** for HTML parsing
- **asyncio** for asynchronous operations

### Performance Requirements:
- **10-15 parallel connections** maximum
- **Delay between requests:** 0.5-1 sec (respectful scraping)
- **Rate limiting:** no more than 30 requests/minute
- **Retry on errors:** 3 attempts with exponential backoff

---

## 📂 Categories to Parse

| Category | URL | Approx. Products |
|----------|-----|------------------|
| Electronics | /collections/electronics | ~150 |
| Audio Technology | /collections/audio-1 | ~80 |
| Office | /collections/office-supplies | ~100 |
| Car Accessories | /collections/car-accessories | ~90 |
| House | /collections/house | ~120 |
| SALE | /collections/sale | ~700 |
| Sport | /collections/sport | ~50 |
| Toys & Games | /collections/toys-games | ~60 |

---

## 📋 Functional Requirements

### 1. Product List Collection
- [ ] Parse all pagination pages in category
- [ ] Extract basic product information
- [ ] Identify promotional products (price_sale != null)
- [ ] Save URLs for detailed parsing

### 2. Detailed Product Parsing
- [ ] Navigate to each product page
- [ ] Extract full description
- [ ] Collect all images
- [ ] Parse technical specifications

### 3. Data Processing
- [ ] Clean prices (remove currency symbols)
- [ ] Normalize text (remove extra spaces)
- [ ] Validate image URLs
- [ ] Calculate discount percentage

### 4. Save Results
- [ ] Export to CSV with correct UTF-8 encoding
- [ ] Export to JSON (structured)
- [ ] Log execution process

---

## 📤 Output Data Format

### CSV Structure:
```csv
product_name,brand,price_regular,price_sale,discount_percent,category,product_url,image_url,sku,in_stock
"AUDIOCORE AC9900 Bluetooth Car Stereo","Audiocore",81.14,60.81,25,"Audio Technology","/products/...","/cdn/shop/...",AC9900,true
```

### JSON Structure:
```json
{
  "scrape_date": "2024-12-15T10:30:00Z",
  "total_products": 723,
  "categories": ["Electronics", "Audio", ...],
  "products": [
    {
      "product_name": "AUDIOCORE AC9900 Bluetooth Car Stereo",
      "brand": "Audiocore",
      "price": {
        "regular": 81.14,
        "sale": 60.81,
        "currency": "EUR",
        "discount_percent": 25
      },
      "category": "Audio Technology",
      "urls": {
        "product": "https://euroelectronics.eu/products/...",
        "images": ["https://..."]
      },
      "sku": "AC9900",
      "in_stock": true,
      "lowest_price_30d": 60.81
    }
  ]
}
```

---

## ✅ Acceptance Criteria

1. Parser successfully collects data from all categories
2. Pagination is handled (all pages processed)
3. Prices are parsed correctly (regular and sale)
4. Data is saved to CSV and JSON without encoding errors
5. Code is documented and maintainable
6. README with launch instructions provided
7. Execution logs are saved to file

---
