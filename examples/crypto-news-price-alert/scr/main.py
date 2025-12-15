from scr.scrapers.coingecko import get_data, get_coins
from scr.analysis.analysis import find_price_changes, news_analysis, convert_to_df
from scr.plugins.save_to import save_digest_markdown, create_comprehensive_json_report
from scr.scrapers.coindesc import get_news

if __name__ == '__main__':
    coins = get_coins(10)
    # Top 10 coins -> list[dict]

    price_changes = get_data(coins, 7)
    # Price movement for the last 7 days -> tuple[df, list[dict]]

    analyzed_price_changes = find_price_changes(price_changes)
    # 1) Analyzed price movement -> tuple[df, list[dict]]
    # 2) Raw CSV output -> "price_changes_summary.csv"

    news = get_news(analyzed_price_changes[1])
    # News for coins with pct_change > 5% -> list[dict]

    after_analyses = news_analysis(news)
    # 1) Analyzed and sorted news -> tuple[df, list[dict]]
    # 2) Raw CSV output -> "sorted_news.csv"

    save_digest_markdown(
        after_analyses[0],
        analyzed_price_changes[0]
    )
    # Markdown digest with price movements and related news

    coins_df = convert_to_df(coins)
    # Convert get_coins() output to DataFrame

    create_comprehensive_json_report(
        coins_df,
        analyzed_price_changes[0],
        after_analyses[0]
    )
    # Comprehensive JSON report with all coins, prices, and news
