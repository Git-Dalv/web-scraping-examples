# API Documentation

## Sreality REST API

This project uses the unofficial Sreality REST API to collect property listings.

## Base URL

```
https://www.sreality.cz/api/v1
```

## Endpoints

### 1. Filter Page

Get reference data (regions, categories, districts).

```
GET /estates/filter_page?lang=cs
```

#### Response

```json
{
  "results": [
    {
      "id_name": "category_type_cb",
      "values": [
        {"id": 1, "name": "Prodej"},
        {"id": 2, "name": "Pronájem"}
      ]
    },
    {
      "id_name": "category_main_cb",
      "values": [
        {"id": 1, "name": "Byty"},
        {"id": 2, "name": "Domy"},
        {"id": 3, "name": "Pozemky"},
        {"id": 4, "name": "Komerční"},
        {"id": 5, "name": "Ostatní"}
      ]
    },
    {
      "id_name": "locality_region_id",
      "values": [
        {"id": 10, "name": "Praha"},
        {"id": 11, "name": "Středočeský kraj"},
        ...
      ]
    },
    {
      "id_name": "locality_district_id",
      "values": [
        {"id": 5001, "name": "Benešov", "region_id": 11},
        ...
      ]
    }
  ]
}
```

### 2. Search Estates

Get property listings with pagination.

```
GET /estates/search?locality_region_id={id}&category_main_cb={cat}&limit={n}&offset={o}&lang=cs
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| locality_region_id | int | Region ID (10=Praha, 11=Středočeský, etc.) |
| category_main_cb | int | Category (1=Byty, 2=Domy, 3=Pozemky, 4=Komerční, 5=Ostatní) |
| category_type_cb | int | Type (1=Prodej, 2=Pronájem) |
| limit | int | Items per request (max 1000) |
| offset | int | Pagination offset (max 10000) |
| lang | string | Language (cs/en) |

#### Response

```json
{
  "pagination": {
    "total": 25432,
    "limit": 1000,
    "offset": 0
  },
  "results": [
    {
      "hash_id": 3476902476,
      "advert_name": "Prodej rodinného domu, 150 m²",
      "price_czk": 8500000,
      "price_czk_m2": 56667,
      "category_type_cb": {"value": 1, "name": "Prodej"},
      "category_main_cb": {"value": 2, "name": "Domy"},
      "category_sub_cb": {"value": 37, "name": "Rodinný"},
      "locality": {
        "city": "Praha",
        "citypart": "Nedvězí",
        "street": "Výtoňská",
        "city_seo_name": "praha",
        "citypart_seo_name": "nedvezi-u-rican",
        "street_seo_name": "vytonska",
        "district_id": 5001,
        "region_id": 10,
        "gps_lat": 50.0123,
        "gps_lon": 14.5678
      },
      "premise_id": 12345,
      "premise": {
        "seo_name": "agency-name"
      },
      "poi_metro_distance": 1500,
      "poi_bus_public_transport_distance": 200,
      "has_video": false,
      "has_matterport_url": false,
      "advert_images": ["https://..."],
      "advert_images_all": [
        {
          "advert_image_sdn_url": "https://...",
          "restb_room_type": 1
        }
      ]
    }
  ]
}
```

## Pagination Strategy

### Problem

Sreality API has a **10,000 offset limit**. Total listings exceed 90,000.

### Solution

1. Split by region (14 regions)
2. For regions with >10,000 listings, split by category (5 categories)
3. Fetch each segment with pagination

```python
for region_id in regions:
    total = get_total(region_id)
    
    if total <= 10000:
        fetch_all(region_id)
    else:
        for category in categories:
            fetch_all(region_id, category)
```

### Implementation

```python
MAX_OFFSET = 10000

def get_all_data(db, step=1000, delay=0.5):
    regions = get_regions(db)
    categories = get_categories(db)
    
    for region_id in regions:
        region_total = get_total(region_id)
        
        if region_total <= MAX_OFFSET:
            fetch_segment(region_id)
        else:
            for cat in categories:
                fetch_segment(region_id, cat)
```

## Rate Limiting

- Default delay: 0.5 seconds between requests
- Retry: 3 attempts with exponential backoff
- Configurable via `config.yaml`

## HTTP Client Configuration

```yaml
# src/configs/config.yaml
base_url: "https://www.sreality.cz"
timeout: 30
retry:
  max_attempts: 3
  backoff_factor: 1.0
headers:
  User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  Accept: "application/json"
  Accept-Language: "cs,en;q=0.9"
```

## URL Construction

Property detail URLs follow this pattern:

```
https://www.sreality.cz/detail/{type}/{main}/{sub}/{locality}/{hash_id}
```

### Components

| Part | Source | Example |
|------|--------|---------|
| type | category_types.seo_name | prodej |
| main | category_main.seo_name | dum |
| sub | category_sub.seo_name | rodinny |
| locality | city_seo-citypart_seo-street_seo | praha-nedvezi-vytonska |
| hash_id | estates.hash_id | 3476902476 |

### Locality Rules

- With street: `{city}-{citypart}-{street}`
- Without street: `{city}-{citypart}-`
- City only: `{city}-{city}-`

### Example

```
https://www.sreality.cz/detail/prodej/dum/rodinny/praha-nedvezi-u-rican-vytonska/3476902476
```

## Error Handling

### HTTP Errors

| Code | Action |
|------|--------|
| 429 | Wait and retry (rate limited) |
| 500-503 | Retry with backoff |
| 404 | Skip (listing removed) |

### API Errors

```python
try:
    response = client.get(url, params=params)
    data = response.json()
except Exception as e:
    logger.error(f"API error: {e}")
    # Retry or skip
```

## Data Freshness

- Full scrape: ~45 minutes for 90,000 listings
- Recommended frequency: Daily
- Price tracking: Automatic on each scrape
- Closed detection: Compare with previous run

## Legal Notes

- Unofficial API - may change without notice
- Respect rate limits
- For personal/educational use
- Consider official API for production
