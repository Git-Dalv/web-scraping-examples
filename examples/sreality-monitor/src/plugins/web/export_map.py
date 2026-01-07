import json
from pathlib import Path
from src.database.db import Database
from src.plugins.logging import create_logger

logger = create_logger(__name__)

OUTPUT_PATH = Path(__file__).parent / "estates.json"


def export_estates(db: Database, output_path: Path = None, limit: int = None):
    if output_path is None:
        output_path = OUTPUT_PATH
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # Get regions for lookup
    cursor.execute("SELECT id, name FROM regions")
    regions = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get category SEO mappings
    cursor.execute("SELECT id, seo_name FROM category_types")
    type_seo = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, seo_name FROM category_main")
    main_seo = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, seo_name FROM category_sub")
    sub_seo = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get estates with coordinates
    query = """
        SELECT 
            hash_id, name, price, price_m2,
            category_type_id, category_main_id, category_sub_id,
            city, citypart, street,
            city_seo, citypart_seo, street_seo,
            region_id, district_id,
            lat, lon,
            status, first_seen_at, closed_at
        FROM estates
        WHERE lat IS NOT NULL AND lon IS NOT NULL
        ORDER BY price DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    estates = []
    for row in rows:
        hash_id = row[0]
        cat_type_id = row[4]
        cat_main_id = row[5]
        cat_sub_id = row[6]
        city_seo = row[10]
        citypart_seo = row[11]
        street_seo = row[12]
        
        # Build URL
        url = build_estate_url(
            hash_id=hash_id,
            type_seo=type_seo.get(cat_type_id, "prodej"),
            main_seo=main_seo.get(cat_main_id, "byt"),
            sub_seo=sub_seo.get(cat_sub_id, ""),
            city_seo=city_seo,
            citypart_seo=citypart_seo,
            street_seo=street_seo
        )
        
        estates.append({
            "hash_id": hash_id,
            "name": row[1],
            "price": row[2],
            "price_m2": row[3],
            "category_type_id": cat_type_id,
            "category_main_id": cat_main_id,
            "category_sub_id": cat_sub_id,
            "city": row[7],
            "citypart": row[8],
            "street": row[9],
            "region_id": row[13],
            "district_id": row[14],
            "lat": row[15],
            "lon": row[16],
            "status": row[17],
            "first_seen_at": row[18],
            "closed_at": row[19],
            "url": url
        })
    
    data = {
        "estates": estates,
        "regions": regions,
        "total": len(estates)
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    
    logger.info(f"Exported {len(estates)} estates to {output_path}")
    
    return len(estates)


def build_estate_url(hash_id, type_seo, main_seo, sub_seo, city_seo, citypart_seo, street_seo):
    if not city_seo:
        locality = "unknown"
    elif street_seo:
        locality = f"{city_seo}-{citypart_seo}-{street_seo}"
    elif citypart_seo:
        locality = f"{city_seo}-{citypart_seo}-"
    else:
        locality = f"{city_seo}-{city_seo}-"
    
    url = f"https://www.sreality.cz/detail/{type_seo}/{main_seo}/{sub_seo}/{locality}/{hash_id}"
    return url


def main():
    with Database() as db:
        export_estates(db)


if __name__ == "__main__":
    main()