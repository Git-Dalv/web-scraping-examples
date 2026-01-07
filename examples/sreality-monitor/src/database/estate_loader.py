import unicodedata
from src.database.db import Database
from src.plugins.logging import create_logger

logger = create_logger(__name__)


class EstateLoader:
    def __init__(self, db: Database):
        self.db = db
        self.estates_count = 0
        self.images_count = 0
        self.premises_count = 0
        self.category_sub_count = 0
        self.price_changes = 0
        self.new_estates = 0
        self.seen_hash_ids = set()
    
    def load_batch(self, results: list):
        conn = self.db.connect()
        cursor = conn.cursor()
        
        for item in results:
            hash_id = item.get("hash_id")
            if hash_id:
                self.seen_hash_ids.add(hash_id)
            
            self._upsert_category_sub(cursor, item)
            self._upsert_premise(cursor, item)
            self._upsert_estate(cursor, item)
            self._insert_images(cursor, item)
        
        conn.commit()
    
    def _upsert_category_sub(self, cursor, item: dict):
        cat_sub = item.get("category_sub_cb", {})
        if cat_sub.get("value") and cat_sub.get("name"):
            # Generate seo_name from name
            seo_name = self._to_seo_name(cat_sub["name"])
            cursor.execute("""
                INSERT OR IGNORE INTO category_sub (id, name, seo_name, category_main_id)
                VALUES (?, ?, ?, ?)
            """, (
                cat_sub["value"],
                cat_sub["name"],
                seo_name,
                item.get("category_main_cb", {}).get("value")
            ))
            if cursor.rowcount > 0:
                self.category_sub_count += 1
    
    def _to_seo_name(self, name: str) -> str:
        if not name:
            return ""
        normalized = unicodedata.normalize('NFKD', name)
        ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
        return ascii_name.lower().replace(" ", "-").replace("+", "-")
    
    def _upsert_premise(self, cursor, item: dict):
        premise_id = item.get("premise_id")
        if not premise_id:
            return
        
        premise = item.get("premise", {})
        cursor.execute("""
            INSERT OR REPLACE INTO premises (id, seo_name, logo, city, quarter, ward)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            premise_id,
            premise.get("seo_name"),
            item.get("premise_logo"),
            premise.get("city_seo_name"),
            premise.get("quarter_seo_name"),
            premise.get("ward_seo_name")
        ))
        if cursor.rowcount > 0:
            self.premises_count += 1
    
    def _upsert_estate(self, cursor, item: dict):
        hash_id = item.get("hash_id")
        new_price = item.get("price_czk")
        new_price_m2 = item.get("price_czk_m2")
        loc = item.get("locality", {})
        
        cursor.execute(
            "SELECT price, price_m2, first_seen_at FROM estates WHERE hash_id = ?",
            (hash_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            old_price, old_price_m2, first_seen = existing
            
            if old_price != new_price or old_price_m2 != new_price_m2:
                cursor.execute("""
                    INSERT INTO price_history (hash_id, price, price_m2)
                    VALUES (?, ?, ?)
                """, (hash_id, old_price, old_price_m2))
                self.price_changes += 1
            
            cursor.execute("""
                UPDATE estates SET
                    name = ?, price = ?, price_m2 = ?,
                    category_type_id = ?, category_main_id = ?, category_sub_id = ?,
                    city = ?, citypart = ?, street = ?, housenumber = ?,
                    city_seo = ?, citypart_seo = ?, street_seo = ?,
                    district_id = ?, region_id = ?, lat = ?, lon = ?,
                    poi_metro = ?, poi_bus = ?, poi_train = ?, poi_school = ?,
                    poi_kindergarten = ?, poi_shop = ?, poi_small_shop = ?,
                    poi_restaurant = ?, poi_medic = ?, poi_vet = ?,
                    poi_atm = ?, poi_post = ?, poi_playground = ?,
                    premise_id = ?, user_id = ?, has_video = ?, has_matterport = ?,
                    status = 'active',
                    last_seen_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE hash_id = ?
            """, (
                item.get("advert_name"),
                new_price,
                new_price_m2,
                item.get("category_type_cb", {}).get("value"),
                item.get("category_main_cb", {}).get("value"),
                item.get("category_sub_cb", {}).get("value"),
                loc.get("city"),
                loc.get("citypart"),
                loc.get("street"),
                loc.get("housenumber"),
                loc.get("city_seo_name"),
                loc.get("citypart_seo_name"),
                loc.get("street_seo_name"),
                loc.get("district_id"),
                loc.get("region_id"),
                loc.get("gps_lat"),
                loc.get("gps_lon"),
                item.get("poi_metro_distance"),
                item.get("poi_bus_public_transport_distance"),
                item.get("poi_train_distance"),
                item.get("poi_school_distance"),
                item.get("poi_kindergarten_distance"),
                item.get("poi_shop_distance"),
                item.get("poi_small_shop_distance"),
                item.get("poi_restaurant_distance"),
                item.get("poi_medic_distance"),
                item.get("poi_vet_distance"),
                item.get("poi_atm_distance"),
                item.get("poi_post_office_distance"),
                item.get("poi_playground_distance"),
                item.get("premise_id"),
                item.get("user_id"),
                int(item.get("has_video", False)),
                int(item.get("has_matterport_url", False)),
                hash_id
            ))
        else:
            cursor.execute("""
                INSERT INTO estates (
                    hash_id, name, price, price_m2,
                    category_type_id, category_main_id, category_sub_id,
                    city, citypart, street, housenumber,
                    city_seo, citypart_seo, street_seo,
                    district_id, region_id, lat, lon,
                    poi_metro, poi_bus, poi_train, poi_school,
                    poi_kindergarten, poi_shop, poi_small_shop,
                    poi_restaurant, poi_medic, poi_vet,
                    poi_atm, poi_post, poi_playground,
                    premise_id, user_id, has_video, has_matterport,
                    status, first_seen_at, last_seen_at
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """, (
                hash_id,
                item.get("advert_name"),
                new_price,
                new_price_m2,
                item.get("category_type_cb", {}).get("value"),
                item.get("category_main_cb", {}).get("value"),
                item.get("category_sub_cb", {}).get("value"),
                loc.get("city"),
                loc.get("citypart"),
                loc.get("street"),
                loc.get("housenumber"),
                loc.get("city_seo_name"),
                loc.get("citypart_seo_name"),
                loc.get("street_seo_name"),
                loc.get("district_id"),
                loc.get("region_id"),
                loc.get("gps_lat"),
                loc.get("gps_lon"),
                item.get("poi_metro_distance"),
                item.get("poi_bus_public_transport_distance"),
                item.get("poi_train_distance"),
                item.get("poi_school_distance"),
                item.get("poi_kindergarten_distance"),
                item.get("poi_shop_distance"),
                item.get("poi_small_shop_distance"),
                item.get("poi_restaurant_distance"),
                item.get("poi_medic_distance"),
                item.get("poi_vet_distance"),
                item.get("poi_atm_distance"),
                item.get("poi_post_office_distance"),
                item.get("poi_playground_distance"),
                item.get("premise_id"),
                item.get("user_id"),
                int(item.get("has_video", False)),
                int(item.get("has_matterport_url", False))
            ))
            self.new_estates += 1
        
        self.estates_count += 1
    
    def _insert_images(self, cursor, item: dict):
        hash_id = item.get("hash_id")
        if not hash_id:
            return
        
        cursor.execute("DELETE FROM estate_images WHERE hash_id = ?", (hash_id,))
        
        images_all = item.get("advert_images_all", [])
        if images_all:
            for pos, img in enumerate(images_all):
                cursor.execute("""
                    INSERT INTO estate_images (hash_id, url, room_type, position)
                    VALUES (?, ?, ?, ?)
                """, (
                    hash_id,
                    img.get("advert_image_sdn_url"),
                    img.get("restb_room_type"),
                    pos
                ))
                self.images_count += 1
        else:
            for pos, url in enumerate(item.get("advert_images", [])):
                cursor.execute("""
                    INSERT INTO estate_images (hash_id, url, room_type, position)
                    VALUES (?, ?, NULL, ?)
                """, (hash_id, url, pos))
                self.images_count += 1
    
    def mark_closed_estates(self):
        conn = self.db.connect()
        cursor = conn.cursor()
        
        if not self.seen_hash_ids:
            return 0
        
        cursor.execute("SELECT hash_id FROM estates WHERE status = 'active'")
        all_active = {row[0] for row in cursor.fetchall()}
        
        not_seen = all_active - self.seen_hash_ids
        
        if not_seen:
            placeholders = ",".join("?" * len(not_seen))
            cursor.execute(f"""
                UPDATE estates 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP
                WHERE hash_id IN ({placeholders})
            """, list(not_seen))
            conn.commit()
        
        return len(not_seen)
    
    def get_stats(self) -> dict:
        return {
            "estates": self.estates_count,
            "new_estates": self.new_estates,
            "price_changes": self.price_changes,
            "images": self.images_count,
            "premises": self.premises_count,
            "category_sub": self.category_sub_count
        }