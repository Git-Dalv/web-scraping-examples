-- Sreality Monitor Database Schema
-- Reference data: /api/v1/estates/filter_page?lang=en

PRAGMA foreign_keys = ON;

-- Reference Tables

CREATE TABLE IF NOT EXISTS category_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    seo_name TEXT
);

CREATE TABLE IF NOT EXISTS category_main (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    seo_name TEXT
);

CREATE TABLE IF NOT EXISTS category_sub (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    seo_name TEXT,
    category_main_id INTEGER,
    FOREIGN KEY (category_main_id) REFERENCES category_main(id)
);

CREATE TABLE IF NOT EXISTS regions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    FOREIGN KEY (region_id) REFERENCES regions(id)
);

-- Main Data

CREATE TABLE IF NOT EXISTS premises (
    id INTEGER PRIMARY KEY,
    seo_name TEXT,
    logo TEXT,
    city TEXT,
    quarter TEXT,
    ward TEXT
);

CREATE TABLE IF NOT EXISTS estates (
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

CREATE TABLE IF NOT EXISTS estate_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    room_type INTEGER,
    position INTEGER,
    FOREIGN KEY (hash_id) REFERENCES estates(hash_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id INTEGER NOT NULL,
    price INTEGER,
    price_m2 INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hash_id) REFERENCES estates(hash_id) ON DELETE CASCADE
);

-- Indexes

CREATE INDEX IF NOT EXISTS idx_estates_city ON estates(city);
CREATE INDEX IF NOT EXISTS idx_estates_district ON estates(district_id);
CREATE INDEX IF NOT EXISTS idx_estates_region ON estates(region_id);
CREATE INDEX IF NOT EXISTS idx_estates_price ON estates(price);
CREATE INDEX IF NOT EXISTS idx_estates_price_m2 ON estates(price_m2);
CREATE INDEX IF NOT EXISTS idx_estates_category ON estates(category_main_id, category_type_id);
CREATE INDEX IF NOT EXISTS idx_estates_location ON estates(lat, lon);
CREATE INDEX IF NOT EXISTS idx_estates_premise ON estates(premise_id);
CREATE INDEX IF NOT EXISTS idx_estates_updated ON estates(updated_at);
CREATE INDEX IF NOT EXISTS idx_estates_status ON estates(status);
CREATE INDEX IF NOT EXISTS idx_estates_last_seen ON estates(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_images_hash ON estate_images(hash_id);
CREATE INDEX IF NOT EXISTS idx_price_history_hash ON price_history(hash_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_districts_region ON districts(region_id);
CREATE INDEX IF NOT EXISTS idx_category_sub_main ON category_sub(category_main_id);