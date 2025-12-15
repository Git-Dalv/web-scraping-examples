from http_client import HTTPClient
import os
from http_client.core.env_config import ConfigFileLoader
from pathlib import Path
import time
from dotenv import load_dotenv
from datetime import datetime


def _create_client() -> HTTPClient:
    load_dotenv()
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "configs" / "coingecko.yaml"
    config = ConfigFileLoader.from_yaml(str(config_path))
    client = HTTPClient(config=config)
    api_key = os.getenv("API_KEY1")

    client.session.headers.update({
        "x-cg-demo-api-key": api_key
    })
    return client


def get_coins(pages: int) -> []:
    coins = []
    with _create_client() as client:
        response = client.get("/coins/markets",
                              params={
                                  'vs_currency': "usd",
                                  'per_page': pages,
                              })
        data = response.json()

        for coin_data in data:
            coin = {
                'id': coin_data['id'],
                'name': coin_data['name'],
                'symbol': coin_data['symbol'],
                "price": coin_data['current_price'],
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M')

            }
            coins.append(coin)
    return coins


def get_data(coins: list, days: int) -> list:
    result = []
    with _create_client() as client:
        for coin in coins:
            response = client.get(f"/coins/{coin['id']}/market_chart",
                                  params={
                                      'vs_currency': 'usd',
                                      'days': days,
                                  })
            data = response.json()
            for timestamp, price in data["prices"]:
                result.append({'id': coin['id'], 'timestamp': timestamp, 'price': price})
            time.sleep(2.5)
    return result
