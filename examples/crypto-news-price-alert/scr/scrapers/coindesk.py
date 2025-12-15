from time import sleep
from http_client import HTTPClient
import os
from http_client.core.env_config import ConfigFileLoader
from pathlib import Path
from dotenv import load_dotenv
from scr.plugins.text_cleaner import clean_text


def _create_client() -> HTTPClient:
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "configs" / "coindesk.yaml"
    config = ConfigFileLoader.from_yaml(str(config_path))
    client = HTTPClient(config=config)

    return client


def get_news(price_moving: [], sleep_time: float = 3.0) -> list[dict]:
    with _create_client() as client:
        load_dotenv()
        api_key = os.getenv("API_KEY2")
        result = []
        for coin in price_moving:
            coin_id = coin["id"]
            to_time = coin["to_time"] // 1000
            pct_change = coin["pct_change"]
            response = client.get(f'/news/v1/search', params={
                "search_string": coin_id,
                "source_key": "coindesk",
                "to_ts": to_time,
                "limit": 2,
                "api_key": api_key
            })
            news = response.json()['Data']
            for new in news:
                result.append({
                    'id': coin_id,
                    'pct_change': pct_change,
                    'sentiment': new['SENTIMENT'],
                    'title': clean_text(new['TITLE']),
                    'subtitle': clean_text(new['SUBTITLE']),
                    'body': clean_text(new['BODY']),
                    'url': new['URL'],
                    'date_s': new['PUBLISHED_ON']
                })
            sleep(sleep_time)
        return result
