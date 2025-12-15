import pandas as pd
import json
from datetime import datetime
from pathlib import Path


def save_digest_markdown(price_moving: pd.DataFrame, news: pd.DataFrame, filename='digest.md') -> None:
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    file_md = reports_dir / filename
    df_merged = pd.merge(
        price_moving,
        news,
        on=['id', 'pct_change'],
        how='left'
    )
    with open(file_md, 'w', encoding='utf-8') as f:
        f.write("# Crypto Price Movement Digest\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        for coin_id in df_merged['id'].unique():
            coin_data = df_merged[df_merged['id'] == coin_id]
            f.write(f"## {coin_id.upper()}\n\n")
            for pct_change in coin_data['pct_change'].unique():
                movement_data = coin_data[coin_data['pct_change'] == pct_change]
                first_row = movement_data.iloc[0]
                f.write(f"### |{first_row['direction']}|: {pct_change:+.2f}%\n\n")
                date_str = datetime.fromtimestamp(first_row['day'] / 1000).strftime('%d.%m.%Y %H:%M')
                f.write(f"**Date:** {date_str}  \n")
                f.write(f"**Price Change:** ${first_row['from_price']:,.2f} → ${first_row['to_price']:,.2f}\n\n")

                if pd.notna(first_row['title']):
                    f.write("#### Related News:\n\n")
                    for _, news in movement_data.iterrows():
                        if pd.notna(news['title']):
                            news_date = datetime.fromtimestamp(news['date_s']).strftime('%d.%m.%Y')
                            f.write(f"**[{news['sentiment']}]** {news['title']}\n")
                            f.write(f"   - *Published:* {news_date}\n")
                            if pd.notna(news['subtitle']):
                                f.write(f"   - *Subtitle:* {news['subtitle']}\n")
                            f.write(f"   - [Read more]({news['url']})\n\n")
                else:
                    f.write("#### No news found for this period\n\n")

                    f.write("---\n\n")
    print(f" Digest saved to {filename}")


def create_comprehensive_json_report(df_coins: pd.DataFrame, df_price: pd.DataFrame, df_news: pd.DataFrame,
                                     output_dir='reports', threshold=5.0):
    """
    Creates a comprehensive JSON report for all monitored coins

    Args:
        df_coins: DataFrame with all monitored coins (from get_coins)
        df_price: DataFrame with significant price changes (from find_price_changes)
        df_news: DataFrame with news articles
        threshold: threshold for "significant" price change (default 5%)
        output_dir: directory for saving report

    Returns:
        dict: json_report dictionary
    """

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = output_path / f'comprehensive_report_{timestamp}.json'

    # Merge price and news data
    if len(df_news) > 0:
        df_merged = pd.merge(df_price, df_news, on=['id', 'pct_change'], how='left')
    else:
        df_merged = df_price.copy()

    # List for JSON report
    all_coins_report = []

    # Iterate through ALL coins from get_coins
    for _, coin in df_coins.iterrows():
        coin_id = coin['id']
        coin_name = coin['name']
        coin_symbol = coin['symbol'].upper()
        current_price = coin['price']

        # Check if there are significant changes for this coin
        coin_movements = df_price[df_price['id'] == coin_id]

        if len(coin_movements) == 0:
            # Coin without significant changes
            coin_report = {
                "coin": coin_name,
                "symbol": coin_symbol,
                "coin_id": coin_id,
                "current_price": float(current_price),
                "status": "normal",
                "message": f"Price movement within normal range (< +/-{threshold}%)",
                "movements": [],
                "total_news": 0,
                "scraped_at": coin['scraped_at']
            }

        else:
            # Coin with significant changes
            movements = []
            total_news = 0
            total_positive = 0
            total_negative = 0
            total_neutral = 0

            for pct_change in coin_movements['pct_change'].unique():
                movement_data = df_merged[
                    (df_merged['id'] == coin_id) &
                    (df_merged['pct_change'] == pct_change)
                    ]

                first_row = movement_data.iloc[0]

                # Determine alert type
                if abs(pct_change) >= threshold:
                    if pct_change > 0:
                        alert_type = "SURGE"
                    else:
                        alert_type = "DROP"
                else:
                    alert_type = "NORMAL"

                # Collect news for this movement
                news_items = movement_data.dropna(
                    subset=['title']) if 'title' in movement_data.columns else pd.DataFrame()

                related_news = []
                news_positive = 0
                news_negative = 0
                news_neutral = 0

                for _, news in news_items.iterrows():
                    sentiment = news['sentiment']

                    if sentiment == 'POSITIVE':
                        news_positive += 1
                    elif sentiment == 'NEGATIVE':
                        news_negative += 1
                    else:
                        news_neutral += 1

                    related_news.append({
                        "title": news['title'],
                        "url": news['url'],
                        "sentiment": sentiment,
                        "published_at": datetime.fromtimestamp(news['date_s']).isoformat() + 'Z'
                    })

                total_news += len(related_news)
                total_positive += news_positive
                total_negative += news_negative
                total_neutral += news_neutral

                # Movement information
                movement_info = {
                    "direction": first_row['direction'],
                    "change_percent": float(pct_change),
                    "from_price": float(first_row['from_price']),
                    "to_price": float(first_row['to_price']),
                    "timestamp": datetime.fromtimestamp(first_row['day'] / 1000).isoformat() + 'Z',
                    "alert_type": alert_type,
                    "news_count": len(related_news),
                    "news_positive": news_positive,
                    "news_negative": news_negative,
                    "news_neutral": news_neutral,
                    "related_news": related_news
                }

                movements.append(movement_info)

            coin_report = {
                "coin": coin_name,
                "symbol": coin_symbol,
                "coin_id": coin_id,
                "current_price": float(current_price),
                "status": "alert",
                "message": f"Significant price movement detected ({len(movements)} movement(s))",
                "movements": movements,
                "total_news": total_news,
                "total_positive": total_positive,
                "total_negative": total_negative,
                "total_neutral": total_neutral,
                "scraped_at": coin['scraped_at']
            }

        all_coins_report.append(coin_report)

    # Create summary statistics
    coins_with_alerts = len([c for c in all_coins_report if c['status'] == 'alert'])
    coins_normal = len([c for c in all_coins_report if c['status'] == 'normal'])
    total_news_count = sum(c['total_news'] for c in all_coins_report)

    # Build final JSON report
    json_report = {
        "generated_at": datetime.now().isoformat() + 'Z',
        "threshold_percent": threshold,
        "summary": {
            "total_coins_monitored": len(df_coins),
            "coins_with_alerts": coins_with_alerts,
            "coins_normal": coins_normal,
            "total_news_articles": total_news_count,
            "total_movements_detected": len(df_price)
        },
        "coins": all_coins_report
    }

    # Save JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)

    print(f"JSON report saved to {json_file}")
    print(f"Total coins: {len(df_coins)}")
    print(f"With alerts: {coins_with_alerts}")
    print(f"Normal: {coins_normal}")
    print(f"Total news: {total_news_count}")

    return json_report
