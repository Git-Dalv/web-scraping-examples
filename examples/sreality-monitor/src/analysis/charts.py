import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.database.db import Database
from src.analysis.analytics import Analytics

# Style settings
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ['#667eea', '#764ba2', '#27ae60', '#f39c12', '#e74c3c', '#3498db', '#9b59b6', '#1abc9c']

OUTPUT_DIR = Path(__file__).parent / "charts"


def setup_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_price(x, pos):
    """Format price for axis labels"""
    if x >= 1_000_000:
        return f'{x/1_000_000:.1f}M'
    elif x >= 1_000:
        return f'{x/1_000:.0f}k'
    return f'{x:.0f}'


def generate_price_by_region_chart(analytics: Analytics) -> Path:
    """Generate bar chart: average price/m2 by region"""
    data = analytics.get_price_by_region()[:10]
    
    if not data:
        return None
    
    regions = [d['region'] for d in data]
    prices = [d['avg_price_m2'] for d in data]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(regions, prices, color=COLORS[0])
    
    ax.set_xlabel('Average Price per m2 (CZK)')
    ax.set_title('Average Price per m2 by Region (Top 10)')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_price))
    
    for bar, price in zip(bars, prices):
        ax.text(bar.get_width() + 1000, bar.get_y() + bar.get_height()/2,
                f'{price:,.0f}', va='center', fontsize=9)
    
    ax.invert_yaxis()
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'price_per_m2_by_region.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_price_distribution_chart(analytics: Analytics) -> Path:
    """Generate histogram: price distribution for sale"""
    data = analytics.get_price_distribution()
    sale_data = data['sale_price']
    
    if not sale_data:
        return None
    
    labels = [d['range'] for d in sale_data]
    counts = [d['count'] for d in sale_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, counts, color=COLORS[1])
    
    ax.set_xlabel('Price Range (CZK)')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Price Distribution (Sale)')
    
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                    f'{count:,}', ha='center', fontsize=9)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'price_distribution.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_price_m2_distribution_chart(analytics: Analytics) -> Path:
    """Generate histogram: price per m2 distribution"""
    data = analytics.get_price_distribution()
    m2_data = data['price_per_m2']
    
    if not m2_data:
        return None
    
    labels = [d['range'] for d in m2_data]
    counts = [d['count'] for d in m2_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, counts, color=COLORS[2])
    
    ax.set_xlabel('Price per m2 (CZK)')
    ax.set_ylabel('Number of Listings')
    ax.set_title('Price per m2 Distribution')
    
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                    f'{count:,}', ha='center', fontsize=9)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'price_per_m2_distribution.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_top_districts_chart(analytics: Analytics) -> Path:
    """Generate bar chart: top districts by listing count"""
    data = analytics.get_top_districts(15)
    
    if not data:
        return None
    
    districts = [f"{d['district']}" for d in data]
    counts = [d['count'] for d in data]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(districts, counts, color=COLORS[3])
    
    ax.set_xlabel('Number of Listings')
    ax.set_title('Top Districts by Listing Count')
    
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f'{count:,}', va='center', fontsize=9)
    
    ax.invert_yaxis()
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'top_districts.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_category_pie_chart(analytics: Analytics) -> Path:
    """Generate pie chart: listings by category"""
    data = analytics.get_price_by_category()[:6]
    
    if not data:
        return None
    
    labels = [f"{d['type']} - {d['category']}" for d in data]
    sizes = [d['count'] for d in data]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        colors=COLORS[:len(data)],
        startangle=90
    )
    
    ax.set_title('Listings by Category')
    
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'category_distribution.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_new_listings_chart(db: Database) -> Path:
    """Generate line chart: new listings over time"""
    conn = db.connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DATE(first_seen_at) as date, COUNT(*) as count
        FROM estates
        WHERE first_seen_at >= DATE('now', '-30 days')
        GROUP BY DATE(first_seen_at)
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if not data:
        return None
    
    dates = [d[0] for d in data]
    counts = [d[1] for d in data]
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, counts, marker='o', color=COLORS[0], linewidth=2, markersize=6)
    ax.fill_between(dates, counts, alpha=0.3, color=COLORS[0])
    
    ax.set_xlabel('Date')
    ax.set_ylabel('New Listings')
    ax.set_title('New Listings Over Time (Last 30 Days)')
    
    plt.xticks(rotation=45, ha='right')
    ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'new_listings_timeline.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_price_by_category_chart(analytics: Analytics) -> Path:
    """Generate grouped bar chart: average price by category"""
    data = analytics.get_price_by_category()[:8]
    
    if not data:
        return None
    
    labels = [f"{d['category']}" for d in data]
    prices = [d['avg_price'] for d in data]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(labels, prices, color=COLORS[4])
    
    ax.set_xlabel('Category')
    ax.set_ylabel('Average Price (CZK)')
    ax.set_title('Average Price by Category')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_price))
    
    for bar, price in zip(bars, prices):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100000,
                f'{price/1_000_000:.1f}M', ha='center', fontsize=9)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    path = OUTPUT_DIR / 'price_by_category.png'
    plt.savefig(path, dpi=150)
    plt.close()
    
    return path


def generate_all_charts(db: Database = None) -> list:
    """Generate all charts and return paths"""
    setup_output_dir()
    
    if db is None:
        db = Database()
        db.connect()
    
    analytics = Analytics(db)
    
    charts = []
    
    print("Generating charts...")
    
    path = generate_price_by_region_chart(analytics)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    path = generate_price_distribution_chart(analytics)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    path = generate_price_m2_distribution_chart(analytics)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    path = generate_top_districts_chart(analytics)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    path = generate_category_pie_chart(analytics)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    path = generate_new_listings_chart(db)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    path = generate_price_by_category_chart(analytics)
    if path:
        charts.append(path)
        print(f"  - {path.name}")
    
    print(f"\nGenerated {len(charts)} charts in {OUTPUT_DIR}")
    
    return charts


def main():
    with Database() as db:
        generate_all_charts(db)


if __name__ == "__main__":
    main()