from pathlib import Path
from datetime import datetime
import pandas as pd
import json

def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


def analyse_it(data: list):
    if not data:
        print("No data to analyze")
        return

    project_root = get_project_root()
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    csv_sale = reports_dir / f'sale_{timestamp}.csv'
    products_to_json = reports_dir / f'products_{timestamp}.json'

    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=['id'])
    df.rename(columns={'name': 'title',
                       'brand': 'author',
                       'price': 'original_price',
                       'fullPrice': 'price',
                       'available': 'availability',
                       },
              inplace=True)
    df['original_price']= df['original_price'].astype(float)
    df['price'] = df['price'].astype(float)
    df['discount_percent'] = (abs(df['price'] - df['original_price']) / df['original_price'] * 100).round(2)
    pos = df.columns.get_loc("price") + 1
    df.insert(pos, 'discount_percent', df.pop('discount_percent'))
    sale_products = df[df['sale'] == True].copy()

    columns_to_keep_sale = [
        'title',
        'author',
        'price',
        'original_price',
        'discount_percent',
        'availability',
        'rating',
        'category',
        'url'
    ]
    sale_products = sale_products[columns_to_keep_sale]
    sale_products.sort_values('availability')
    sale_products.to_csv(csv_sale, index=False, encoding='utf-8')

    df = df.drop(columns=['tax', "position", "variantId", "id", "sale"])
    with open(products_to_json, 'w', encoding='utf-8') as f:
        json.dump(df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

    top_discounts = df.nlargest(10, 'discount_percent')[columns_to_keep_sale]
    top_discounts.to_csv(reports_dir / f'top10_discounts_{timestamp}.csv', index=False, encoding='utf-8')

    top_cheapest = df.nsmallest(10, 'price')[columns_to_keep_sale]
    top_cheapest.to_csv(reports_dir / f'top10_cheapest_{timestamp}.csv', index=False, encoding='utf-8')

    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    top_rated = df.nlargest(10, 'rating')[columns_to_keep_sale]
    top_rated.to_csv(reports_dir / f'top10_rated_{timestamp}.csv', index=False, encoding='utf-8')

