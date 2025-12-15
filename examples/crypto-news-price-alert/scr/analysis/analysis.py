import pandas as pd


def find_price_changes(
        data: list,
        threshold: float = 0.05
) -> []:
    """[{'id':coin['id'],'timestamp':timestamp, 'price':price},...]"""

    events = []
    price_changes = []

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df["day"] = df["timestamp"].dt.date
    df = df.sort_values(["id", "timestamp"]).reset_index(drop=True)

    for coin_id, group in df.groupby("id"):
        prices = group["price"].values
        timestamps = group["timestamp"].values
        n = len(prices)

        if n < 2:
            continue

        i = 0  # start point

        while i < n - 1:
            p0, t0 = prices[i], timestamps[i]

            for j in range(i + 1, n):
                p1, t1 = prices[j], timestamps[j]
                pct = (p1 - p0) / p0

                if abs(pct) >= threshold:
                    temp = {
                        "id": coin_id,
                        "from_time": t0,
                        "to_time": t1,
                        "from_price": round(p0, 4),
                        "to_price": round(p1, 4),
                        "pct_change": round(pct * 100, 2),
                        "direction": "UP" if pct > 0 else "DOWN"
                    }

                    events.append({
                        "id": coin_id,
                        "day": pd.Timestamp(t0).date(),
                        "from_time": t0,
                        "to_time": t1,
                        "from_price": round(p0, 2),
                        "to_price": round(p1, 2),
                        "pct_change": round(pct * 100, 2),
                        "direction": "UP" if pct > 0 else "DOWN"
                    })

                    price_changes.append(temp)
                    i = j
                    break
            else:
                i += 1

    data = pd.DataFrame(events)

    if len(data) > 0:
        columns_to_convert = ["from_time", "to_time", 'day']

        for col in columns_to_convert:
            data[col] = pd.to_datetime(data[col]).astype('int64') // 10 ** 6

        pd.DataFrame(price_changes).to_csv('price_changes_summary.csv', index=False, encoding="utf-8")

    return [data, data.to_dict(orient='records')]


def news_analysis(news: list):
    df_news = pd.DataFrame(news)
    df_news["date_ms"] = pd.to_datetime(df_news["date_s"], unit="s")
    df_news.rename(columns={"date_ms": "date"}, inplace=True)

    df_news = (df_news
               .groupby(["id", "pct_change"], group_keys=False)
               .apply(lambda x: x.sort_values("date"))
               .reset_index(drop=True))
    df_news.to_csv("sorted_news.csv", index=False, encoding="utf-8")

    return [df_news, df_news.to_dict(orient="records")]


def convert_to_df(all_coins: list) -> pd.DataFrame:
    df = pd.DataFrame(all_coins)
    return df
