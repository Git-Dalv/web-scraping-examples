# Database Schema

SQLite database with normalized schema for storing real estate data.

## Overview

| Table | Records | Description |
|-------|---------|-------------|
| `category_types` | 4 | Transaction types (sale/rent) |
| `category_main` | 5 | Property categories |
| `category_sub` | ~50 | Property subtypes |
| `regions` | 14 | Czech regions |
| `districts` | 77 | Districts within regions |
| `premises` | ~3,000 | Real estate agencies |
| `estates` | ~90,000 | Property listings |
| `estate_images` | ~1,300,000 | Property photos |
| `price_history` | Variable | Price change records |

## Entity Relationship

```
+------------------+       +------------------+
|  category_types  |       |  category_main   |
+------------------+       +------------------+
| id (PK)          |       | id (PK)          |
| name             |       | name             |
| seo_name         |       | seo_name         |
+------------------+       +------------------+
         |                          |
         |    +------------------+  |
         |    |  category_sub    |  |
         |    +------------------+  |
         |    | id (PK)          |<-+
         |    | name             |
         |    | seo_name         |
         |    | category_main_id |
         |    +------------------+
         |             |
         v             v
+------------------------------------------------+
|                    estates                      |
+------------------------------------------------+
| hash_id (PK)                                   |
| name, price, price_m2                          |
| category_type_id (FK) -----------------------> |
| category_main_id (FK) -----------------------> |
| category_sub_id (FK) ------------------------> |
| city, citypart, street, housenumber            |
| city_seo, citypart_seo, street_seo             |
| district_id (FK), region_id (FK)               |
| lat, lon                                       |
| poi_* (distances)                              |
| premise_id (FK), user_id                       |
| has_video, has_matterport                      |
| status, first_seen_at, last_seen_at, closed_at |
+------------------------------------------------+
         |                    |
         v                    v
+------------------+  +------------------+
|  estate_images   |  |  price_history   |
+------------------+  +------------------+
| id (PK)          |  | id (PK)          |
| hash_id (FK)     |  | hash_id (FK)     |
| url              |  | price            |
| room_type        |  | price_m2         |
| position         |  | recorded_at      |
+------------------+  +------------------+

+------------------+       +------------------+
|     regions      |       |    districts     |
+------------------+       +------------------+
| id (PK)          |<------| id (PK)          |
| name             |       | name             |
+------------------+       | region_id (FK)   |
                           +------------------+

+------------------+
|    premises      |
+------------------+
| id (PK)          |
| seo_name         |
| logo             |
| city, quarter    |
| ward             |
+------------------+
```

## Tables

### category_types

Transaction types (prodej/pronajem).

```sql
CREATE TABLE category_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    seo_name TEXT
);
```

| id | name | seo_name |
|----|------|----------|
| 1 | Prodej | prodej |
| 2 | Pronajem | pronajem |
| 3 | Drazby | drazby |
| 4 | Podily | podily |

### category_main

Property categories.

```sql
CREATE TABLE category_main (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    seo_name TEXT
);
```

| id | name | seo_name |
|----|------|----------|
| 1 | Byty | byt |
| 2 | Domy | dum |
| 3 | Pozemky | pozemek |
| 4 | Komercni | komercni |
| 5 | Ostatni | ostatni |

### category_sub

Property subtypes with parent reference.

```sql
CREATE TABLE category_sub (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    seo_name TEXT,
    category_main_id INTEGER,
    FOREIGN KEY (category_main_id) REFERENCES category_main(id)
);
```

Examples:

| id | name | seo_name | category_main_id |
|----|------|----------|------------------|
| 2 | 1+kk | 1-kk | 1 |
| 3 | 1+1 | 1-1 | 1 |
| 4 | 2+kk | 2-kk | 1 |
| 37 | Rodinny | rodinny | 2 |

### regions

Czech regions (kraje).

```sql
CREATE TABLE regions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
```

| id | name |
|----|------|
| 10 | Praha |
| 11 | Stredocesky kraj |
| 12 | Jihocesky kraj |
| ... | ... |

### districts

Districts (okresy) within regions.

```sql
CREATE TABLE districts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    FOREIGN KEY (region_id) REFERENCES regions(id)
);
```

### premises

Real estate agencies.

```sql
CREATE TABLE premises (
    id INTEGER PRIMARY KEY,
    seo_name TEXT,
    logo TEXT,
    city TEXT,
    quarter TEXT,
    ward TEXT
);
```

### estates

Main property listings table.

```sql
CREATE TABLE estates (
    hash_id INTEGER PRIMARY KEY,
    name TEXT,
    price INTEGER,
    price_m2 INTEGER,
    category_type_id INTEGER,
    category_main_id INTEGER,
    category_sub_id INTEGER,
    city TEXT,
    citypart TEXT,
    street TEXT,
    housenumber TEXT,
    city_seo TEXT,
    citypart_seo TEXT,
    street_seo TEXT,
    district_id INTEGER,
    region_id INTEGER,
    lat REAL,
    lon REAL,
    poi_metro INTEGER,
    poi_bus INTEGER,
    poi_train INTEGER,
    poi_school INTEGER,
    poi_kindergarten INTEGER,
    poi_shop INTEGER,
    poi_small_shop INTEGER,
    poi_restaurant INTEGER,
    poi_medic INTEGER,
    poi_vet INTEGER,
    poi_atm INTEGER,
    poi_post INTEGER,
    poi_playground INTEGER,
    premise_id INTEGER,
    user_id INTEGER,
    has_video INTEGER DEFAULT 0,
    has_matterport INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Fields Description

| Field | Type | Description |
|-------|------|-------------|
| hash_id | INTEGER | Unique property ID from API |
| name | TEXT | Property title |
| price | INTEGER | Price in CZK |
| price_m2 | INTEGER | Price per square meter |
| category_type_id | INTEGER | FK to category_types |
| category_main_id | INTEGER | FK to category_main |
| category_sub_id | INTEGER | FK to category_sub |
| city | TEXT | City name (display) |
| citypart | TEXT | District name (display) |
| street | TEXT | Street name (display) |
| city_seo | TEXT | City SEO slug |
| citypart_seo | TEXT | District SEO slug |
| street_seo | TEXT | Street SEO slug |
| lat, lon | REAL | GPS coordinates |
| poi_* | INTEGER | Distance to POI in meters |
| premise_id | INTEGER | FK to premises (agency) |
| status | TEXT | 'active' or 'closed' |
| first_seen_at | TIMESTAMP | First scrape time |
| last_seen_at | TIMESTAMP | Last scrape time |
| closed_at | TIMESTAMP | When listing disappeared |

### estate_images

Property photos.

```sql
CREATE TABLE estate_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    room_type INTEGER,
    position INTEGER,
    FOREIGN KEY (hash_id) REFERENCES estates(hash_id) ON DELETE CASCADE
);
```

### price_history

Historical price changes.

```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id INTEGER NOT NULL,
    price INTEGER,
    price_m2 INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hash_id) REFERENCES estates(hash_id) ON DELETE CASCADE
);
```

## Indexes

```sql
CREATE INDEX idx_estates_city ON estates(city);
CREATE INDEX idx_estates_district ON estates(district_id);
CREATE INDEX idx_estates_region ON estates(region_id);
CREATE INDEX idx_estates_price ON estates(price);
CREATE INDEX idx_estates_price_m2 ON estates(price_m2);
CREATE INDEX idx_estates_category ON estates(category_main_id, category_type_id);
CREATE INDEX idx_estates_location ON estates(lat, lon);
CREATE INDEX idx_estates_premise ON estates(premise_id);
CREATE INDEX idx_estates_updated ON estates(updated_at);
CREATE INDEX idx_estates_status ON estates(status);
CREATE INDEX idx_estates_last_seen ON estates(last_seen_at);
CREATE INDEX idx_images_hash ON estate_images(hash_id);
CREATE INDEX idx_price_history_hash ON price_history(hash_id);
CREATE INDEX idx_price_history_date ON price_history(recorded_at);
CREATE INDEX idx_districts_region ON districts(region_id);
CREATE INDEX idx_category_sub_main ON category_sub(category_main_id);
```

## URL Construction

Property URLs are built from SEO fields:

```
https://www.sreality.cz/detail/{type_seo}/{main_seo}/{sub_seo}/{locality}/{hash_id}
```

Locality format:
- With street: `{city_seo}-{citypart_seo}-{street_seo}`
- With citypart: `{city_seo}-{citypart_seo}-`
- City only: `{city_seo}-{city_seo}-`

Example:
```
https://www.sreality.cz/detail/prodej/dum/rodinny/praha-praha-/3476902476
```

## Queries

### Statistics

```sql
-- Total active listings
SELECT COUNT(*) FROM estates WHERE status = 'active';

-- Average price by region
SELECT r.name, AVG(e.price_m2) as avg_price_m2
FROM estates e
JOIN regions r ON e.region_id = r.id
WHERE e.status = 'active' AND e.price_m2 > 0
GROUP BY r.id
ORDER BY avg_price_m2 DESC;

-- Price changes today
SELECT e.name, e.city, ph.price as old, e.price as new
FROM price_history ph
JOIN estates e ON ph.hash_id = e.hash_id
WHERE DATE(ph.recorded_at) = DATE('now')
ORDER BY ph.recorded_at DESC;

-- New listings today
SELECT * FROM estates
WHERE DATE(first_seen_at) = DATE('now')
AND status = 'active';

-- Closed listings
SELECT * FROM estates
WHERE status = 'closed'
ORDER BY closed_at DESC;
```

## Database Location

```
src/data/sreality.db
```

Approximate size: ~150 MB with 90,000 properties and 1.3M images.
