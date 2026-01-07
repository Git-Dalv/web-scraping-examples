
import sqlite3
from pathlib import Path
from typing import Optional
from src.plugins.logging import create_logger

logger = create_logger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "sreality.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # FK disabled - API data may reference missing lookups
            self.conn.execute("PRAGMA foreign_keys = OFF")
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_schema(self):
        conn = self.connect()
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        logger.info(f"Schema initialized: {self.db_path}")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class FilterPageLoader:
    
    # SEO mappings for URL building
    CATEGORY_TYPE_SEO = {
        1: "prodej",
        2: "pronajem",
        3: "drazby",
        4: "podily"
    }
    
    CATEGORY_MAIN_SEO = {
        1: "byt",
        2: "dum",
        3: "pozemek",
        4: "komercni",
        5: "ostatni"
    }
    
    def __init__(self, db: Database, data: dict):
        self.db = db
        self.data = data
    
    def parse_results(self) -> dict:
        parsed = {}
        for item in self.data.get("results", []):
            id_name = item.get("id_name")
            values = item.get("values", [])
            if id_name and values:
                parsed[id_name] = values
        return parsed
    
    def load_category_types(self, values: list):
        conn = self.db.connect()
        cursor = conn.cursor()
        for item in values:
            seo_name = self.CATEGORY_TYPE_SEO.get(item["id"])
            cursor.execute(
                "INSERT OR REPLACE INTO category_types (id, name, seo_name) VALUES (?, ?, ?)",
                (item["id"], item["name"], seo_name)
            )
        conn.commit()
        logger.info(f"Loaded {len(values)} category types")
    
    def load_category_main(self, values: list):
        conn = self.db.connect()
        cursor = conn.cursor()
        for item in values:
            seo_name = self.CATEGORY_MAIN_SEO.get(item["id"])
            cursor.execute(
                "INSERT OR REPLACE INTO category_main (id, name, seo_name) VALUES (?, ?, ?)",
                (item["id"], item["name"], seo_name)
            )
        conn.commit()
        logger.info(f"Loaded {len(values)} main categories")
    
    def load_regions(self, values: list):
        conn = self.db.connect()
        cursor = conn.cursor()
        for item in values:
            cursor.execute(
                "INSERT OR REPLACE INTO regions (id, name) VALUES (?, ?)",
                (item["id"], item["name"])
            )
        conn.commit()
        logger.info(f"Loaded {len(values)} regions")
    
    def load_districts(self, values: list):
        conn = self.db.connect()
        cursor = conn.cursor()
        for item in values:
            cursor.execute(
                "INSERT OR REPLACE INTO districts (id, name, region_id) VALUES (?, ?, ?)",
                (item["id"], item["name"], item["region_id"])
            )
        conn.commit()
        logger.info(f"Loaded {len(values)} districts")
    
    def load_all(self):
        logger.info("=" * 50)
        logger.info("Loading reference data from filter_page")
        logger.info("=" * 50)
        
        parsed = self.parse_results()
        
        if "category_type_cb" in parsed:
            self.load_category_types(parsed["category_type_cb"])
        
        if "category_main_cb" in parsed:
            self.load_category_main(parsed["category_main_cb"])
        
        if "locality_region_id" in parsed:
            self.load_regions(parsed["locality_region_id"])
        
        if "locality_district_id" in parsed:
            self.load_districts(parsed["locality_district_id"])
        
        logger.info("Reference data loading complete!")
        return parsed


def show_stats():
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        
        tables = [
            "category_types", "category_main", "category_sub",
            "regions", "districts", "premises",
            "estates", "estate_images", "price_history"
        ]
        
        print("\n" + "=" * 40)
        print("DATABASE STATISTICS")
        print("=" * 40)
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20} {count:>10} records")
        
        print("=" * 40)


if __name__ == "__main__":
    show_stats()