# scr/main.py
from __future__ import annotations

import argparse
from typing import NoReturn

from scr.scrapers.coingecko import get_coins, get_data
from scr.scrapers.coindesk import get_news
from scr.analysis.analysis import find_price_changes, news_analysis, convert_to_df
from scr.plugins.save_to import save_digest_markdown, create_comprehensive_json_report


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    p = argparse.ArgumentParser(description="Crypto News + Price Alert digest generator")
    p.add_argument("--top", type=int, default=10, help="Top N coins to monitor (default: 10)")
    p.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    p.add_argument("--threshold", type=float, default=0.05, help="Alert threshold in percent"
                                                                 "(default: 0.05 -> 5% |100% = 1.00|)")
    return p.parse_args()


def main() -> int:
    """Main execution flow"""
    args = parse_args()

    # Fetch top coins
    print(f"Fetching top {args.top} coins...")
    coins = get_coins(args.top)
    print("1: \n", coins)
    # Top N coins -> list[dict]

    # Fetch historical price data
    print(f"Fetching price data for last {args.days} days...")
    price_changes = get_data(coins, args.days)
    print("2: \n", price_changes)
    # Price movement for the last 7 days -> tuple[df, list[dict]]

    # Detect significant price movements
    print(f"Analyzing price changes (threshold: +/-{args.threshold * 100}%)...")
    analyzed_price_changes = find_price_changes(price_changes, threshold=args.threshold)
    print("3: \n", analyzed_price_changes)
    # 1) Analyzed price movement -> tuple[df, list[dict]]
    # 2) Raw CSV output -> "price_changes_summary.csv"

    # Fetch and analyze news
    if len(analyzed_price_changes[1]) == 0:
        print("No significant price movements detected.")
        # Create empty news DataFrame
        after_analyses = (convert_to_df([]), [])
    else:
        print(f"Fetching news for {len(analyzed_price_changes[1])} price movements...")
        news = get_news(analyzed_price_changes[1])
        # News for coins with pct_change > 5% -> list[dict]

        print("Analyzing news articles...")
        after_analyses = news_analysis(news)
        # 1) Analyzed and sorted news -> tuple[df, list[dict]]
        # 2) Raw CSV output -> "sorted_news.csv"

    # Save outputs
    print("Generating reports...")

    # Save Markdown digest

    save_digest_markdown(
        after_analyses[0],  # df_news (first argument in your original)
        analyzed_price_changes[0]  # df_price (second argument in your original)
    )
    # Markdown digest with price movements and related news

    # Convert coins to DataFrame
    coins_df = convert_to_df(coins)
    # Convert get_coins() output to DataFrame

    # Save comprehensive JSON report
    create_comprehensive_json_report(
        coins_df,  # df_coins
        analyzed_price_changes[0],  # df_price
        after_analyses[0],  # df_news
        threshold=args.threshold
    )
    # Comprehensive JSON report with all coins, prices, and news

    print("Reports generated successfully!")
    return 0


def entrypoint() -> NoReturn:
    """Entry point for script execution"""
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
