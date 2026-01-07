
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.database.db import Database
from src.plugins.logging import create_logger

logger = create_logger(__name__)

OUTPUT_PATH = Path(__file__).parent.parent / "plugins" / "web" / "analytics.json"


class Analytics:
    def __init__(self, db: Database):
        self.db = db
        self.conn = db.connect()
    
    def generate_all(self) -> dict:
        """Generate all analytics data"""
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "price_by_region": self.get_price_by_region(),
            "price_by_category": self.get_price_by_category(),
            "price_distribution": self.get_price_distribution(),
            "top_districts": self.get_top_districts(),
            "listings_dynamics": self.get_listings_dynamics(),
            "price_changes": self.get_recent_price_changes(),
            "new_listings": self.get_new_listings_stats(),
        }
    
    def get_summary(self) -> dict:
        """Overall statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM estates WHERE status = 'active'")
        active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM estates WHERE status = 'closed'")
        closed = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT AVG(price), AVG(price_m2), MIN(price), MAX(price)
            FROM estates WHERE status = 'active' AND price > 0
        """)
        row = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM price_history")
        price_changes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT premise_id) FROM estates WHERE premise_id IS NOT NULL")
        agencies = cursor.fetchone()[0]
        
        return {
            "total_active": active,
            "total_closed": closed,
            "avg_price": int(row[0]) if row[0] else 0,
            "avg_price_m2": int(row[1]) if row[1] else 0,
            "min_price": row[2] or 0,
            "max_price": row[3] or 0,
            "total_price_changes": price_changes,
            "total_agencies": agencies
        }
    
    def get_price_by_region(self) -> list:
        """Average price per m² by region"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                r.name,
                r.id,
                COUNT(*) as count,
                AVG(e.price_m2) as avg_price_m2,
                AVG(e.price) as avg_price,
                MIN(e.price) as min_price,
                MAX(e.price) as max_price
            FROM estates e
            JOIN regions r ON e.region_id = r.id
            WHERE e.status = 'active' AND e.price_m2 > 0
            GROUP BY r.id
            ORDER BY avg_price_m2 DESC
        """)
        
        return [
            {
                "region": row[0],
                "region_id": row[1],
                "count": row[2],
                "avg_price_m2": int(row[3]),
                "avg_price": int(row[4]),
                "min_price": row[5],
                "max_price": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def get_price_by_category(self) -> list:
        """Average price by category type and main"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                ct.name as type_name,
                cm.name as main_name,
                COUNT(*) as count,
                AVG(e.price) as avg_price,
                AVG(e.price_m2) as avg_price_m2
            FROM estates e
            JOIN category_types ct ON e.category_type_id = ct.id
            JOIN category_main cm ON e.category_main_id = cm.id
            WHERE e.status = 'active' AND e.price > 0
            GROUP BY ct.id, cm.id
            ORDER BY count DESC
        """)
        
        return [
            {
                "type": row[0],
                "category": row[1],
                "count": row[2],
                "avg_price": int(row[3]),
                "avg_price_m2": int(row[4]) if row[4] else 0
            }
            for row in cursor.fetchall()
        ]
    
    def get_price_distribution(self) -> dict:
        """Price distribution for histograms"""
        cursor = self.conn.cursor()
        
        # Price ranges for sale
        sale_ranges = [
            (0, 1000000, "< 1M"),
            (1000000, 2000000, "1-2M"),
            (2000000, 3000000, "2-3M"),
            (3000000, 5000000, "3-5M"),
            (5000000, 10000000, "5-10M"),
            (10000000, 20000000, "10-20M"),
            (20000000, 999999999, "> 20M"),
        ]
        
        sale_dist = []
        for min_p, max_p, label in sale_ranges:
            cursor.execute("""
                SELECT COUNT(*) FROM estates 
                WHERE status = 'active' 
                AND category_type_id = 1 
                AND price >= ? AND price < ?
            """, (min_p, max_p))
            sale_dist.append({"range": label, "count": cursor.fetchone()[0]})
        
        # Price per m² ranges
        m2_ranges = [
            (0, 30000, "< 30k"),
            (30000, 50000, "30-50k"),
            (50000, 75000, "50-75k"),
            (75000, 100000, "75-100k"),
            (100000, 150000, "100-150k"),
            (150000, 200000, "150-200k"),
            (200000, 999999999, "> 200k"),
        ]
        
        m2_dist = []
        for min_p, max_p, label in m2_ranges:
            cursor.execute("""
                SELECT COUNT(*) FROM estates 
                WHERE status = 'active' 
                AND price_m2 >= ? AND price_m2 < ?
            """, (min_p, max_p))
            m2_dist.append({"range": label, "count": cursor.fetchone()[0]})
        
        return {
            "sale_price": sale_dist,
            "price_per_m2": m2_dist
        }
    
    def get_top_districts(self, limit: int = 20) -> list:
        """Top districts by listing count and price"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                d.name,
                r.name as region_name,
                COUNT(*) as count,
                AVG(e.price_m2) as avg_price_m2,
                AVG(e.price) as avg_price
            FROM estates e
            JOIN districts d ON e.district_id = d.id
            JOIN regions r ON d.region_id = r.id
            WHERE e.status = 'active' AND e.price_m2 > 0
            GROUP BY d.id
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "district": row[0],
                "region": row[1],
                "count": row[2],
                "avg_price_m2": int(row[3]),
                "avg_price": int(row[4])
            }
            for row in cursor.fetchall()
        ]
    
    def get_listings_dynamics(self, days: int = 30) -> dict:
        """New and closed listings over time"""
        cursor = self.conn.cursor()
        
        # New listings by day
        cursor.execute("""
            SELECT DATE(first_seen_at) as date, COUNT(*) as count
            FROM estates
            WHERE first_seen_at >= DATE('now', ?)
            GROUP BY DATE(first_seen_at)
            ORDER BY date
        """, (f'-{days} days',))
        
        new_by_day = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Closed listings by day
        cursor.execute("""
            SELECT DATE(closed_at) as date, COUNT(*) as count
            FROM estates
            WHERE closed_at >= DATE('now', ?) AND status = 'closed'
            GROUP BY DATE(closed_at)
            ORDER BY date
        """, (f'-{days} days',))
        
        closed_by_day = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        return {
            "new_listings": new_by_day,
            "closed_listings": closed_by_day
        }
    
    def get_recent_price_changes(self, limit: int = 50) -> list:
        """Recent price changes"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.hash_id,
                e.name,
                e.city,
                ph.price as old_price,
                e.price as new_price,
                ph.recorded_at,
                ROUND((e.price - ph.price) * 100.0 / ph.price, 1) as change_pct
            FROM price_history ph
            JOIN estates e ON ph.hash_id = e.hash_id
            WHERE ph.price > 0
            ORDER BY ph.recorded_at DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "hash_id": row[0],
                "name": row[1],
                "city": row[2],
                "old_price": row[3],
                "new_price": row[4],
                "recorded_at": row[5],
                "change_pct": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def get_new_listings_stats(self, days: int = 7) -> dict:
        """Statistics for new listings in last N days"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM estates
            WHERE first_seen_at >= DATE('now', ?)
        """, (f'-{days} days',))
        total_new = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT cm.name, COUNT(*) as count
            FROM estates e
            JOIN category_main cm ON e.category_main_id = cm.id
            WHERE e.first_seen_at >= DATE('now', ?)
            GROUP BY cm.id
            ORDER BY count DESC
        """, (f'-{days} days',))
        
        by_category = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT r.name, COUNT(*) as count
            FROM estates e
            JOIN regions r ON e.region_id = r.id
            WHERE e.first_seen_at >= DATE('now', ?)
            GROUP BY r.id
            ORDER BY count DESC
            LIMIT 5
        """, (f'-{days} days',))
        
        top_regions = [{"region": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        return {
            "period_days": days,
            "total_new": total_new,
            "by_category": by_category,
            "top_regions": top_regions
        }


def export_analytics(db: Database, output_path: Path = None):
    """Export analytics to JSON file"""
    if output_path is None:
        output_path = OUTPUT_PATH
    
    analytics = Analytics(db)
    data = analytics.generate_all()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Analytics exported to {output_path}")
    
    return data


def print_summary(db: Database):
    """Print analytics summary to console"""
    analytics = Analytics(db)
    
    print("\n" + "=" * 60)
    print("SREALITY ANALYTICS")
    print("=" * 60)
    
    # Summary
    summary = analytics.get_summary()
    print(f"\n📊 SUMMARY")
    print(f"   Active listings: {summary['total_active']:,}")
    print(f"   Closed listings: {summary['total_closed']:,}")
    print(f"   Avg price: {summary['avg_price']:,} CZK")
    print(f"   Avg price/m²: {summary['avg_price_m2']:,} CZK")
    print(f"   Price changes tracked: {summary['total_price_changes']:,}")
    print(f"   Real estate agencies: {summary['total_agencies']:,}")
    
    # Top regions by price
    print(f"\n🏆 TOP REGIONS BY PRICE/m²")
    for item in analytics.get_price_by_region()[:5]:
        print(f"   {item['region']}: {item['avg_price_m2']:,} CZK/m² ({item['count']:,} listings)")
    
    # Top districts
    print(f"\n📍 TOP DISTRICTS BY LISTINGS")
    for item in analytics.get_top_districts(5):
        print(f"   {item['district']} ({item['region']}): {item['count']:,} listings")
    
    # Category breakdown
    print(f"\n🏠 BY CATEGORY")
    for item in analytics.get_price_by_category()[:6]:
        print(f"   {item['type']} - {item['category']}: {item['count']:,} ({item['avg_price']:,} CZK)")
    
    # New listings
    new_stats = analytics.get_new_listings_stats(7)
    print(f"\n🆕 NEW LISTINGS (last 7 days): {new_stats['total_new']:,}")
    
    print("\n" + "=" * 60)


def main():
    with Database() as db:
        print_summary(db)
        export_analytics(db)


if __name__ == "__main__":
    main()
