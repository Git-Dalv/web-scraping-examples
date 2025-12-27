import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import gzip


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
    products_to_csv = reports_dir / f'products_{timestamp}.csv'

    clean_data = []
    for item in data:
        images = item.get('details', {}).get('image_url', [])
        clean_item = {
            'sale': item.get('sale'),
            'product_name': item.get('product_name'),
            'vendor': item.get('vendor'),
            'in_stock': item.get('in_stock'),
            'price_regular': item.get('price', {}).get('price_regular'),
            'price_sale': item.get('price', {}).get('price_sale'),
            'discount_percent': item.get('price', {}).get('discount_percent'),
            'currency': item.get('price', {}).get('ISO'),
            'category': item.get('category'),
            'product_url': item.get('product_url'),
            'SKU': item.get('details', {}).get('SKU'),
            'lowest_price_30d': item.get('details', {}).get('lowest_price_30d'),
            'image_url': images[0] if images else '',
        }
        clean_data.append(clean_item)

    df = pd.DataFrame(clean_data)
    df = df.drop_duplicates(subset=['SKU'])

    sale_products = df[df['sale'] == True].copy()
    columns_to_keep_sale = [
        'SKU',
        'product_name',
        'vendor',
        'price_regular',
        'price_sale',
        'discount_percent',
        'category',
        'product_url'
    ]

    sale_products = sale_products[columns_to_keep_sale]
    sale_products.sort_values(by='discount_percent', ascending=False, inplace=True)
    sale_products.to_csv(csv_sale, index=False, encoding='utf-8')

    columns_to_keep_product = [
        'SKU',
        'product_name',
        'vendor',
        'price_regular',
        'category',
        'product_url'
    ]
    products = df.copy()
    products = products[columns_to_keep_product]

    products.sort_values('category').to_csv(products_to_csv, index=False, encoding='utf-8')

    print(f"  - Done: {csv_sale} ({len(sale_products)} products)")
    print(f"  - Done (CSV): {products_to_csv} ({len(products)} products)")


def save_to_json(data):
    if not data:
        print("No data to analyze")
        return

    project_root = get_project_root()
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_to_json = reports_dir / f'all_{timestamp}.json.gz'

    with gzip.open(all_to_json, 'wt', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print(f"  - Done(JSON): {all_to_json} ({len(data)} products)")