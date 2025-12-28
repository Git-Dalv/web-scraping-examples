from src.plugins.to_dict import parse_product_info
from src.plugins.cleaner import parse_price

from http_client import HTTPClient
from http_client.core.env_config import ConfigFileLoader
from text_cleaner import clean

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

import time


def _create_client() -> HTTPClient:
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config" / "config.yaml"
    config = ConfigFileLoader.from_yaml(str(config_path))
    client = HTTPClient(config=config)

    return client


def scrape(path: str):
    with _create_client() as client:
        result = []
        url = path
        while True:
            try:
                response = client.get(url)
                bs = BeautifulSoup(response.text, "html.parser")
                main_part = bs.find("main")
                row_cols_part = main_part.find("div", attrs={"class": "col col-content"})
                data_product_part = row_cols_part.find('ul', class_="reset")

                products_list = data_product_part.find_all("li")
                for product in products_list:
                    h = product.find(['h1', 'h2', 'h3'])
                    product_url = h.find('a')['href']
                    product_data = product['data-productinfo']
                    current_data = parse_product_info(product_data)
                    current_data['url'] = urljoin(client.base_url, product_url)

                    price_wrap = product.find("div", class_="price-wrap")
                    full_price = price_wrap.find("strong")
                    if not full_price:
                        continue
                    full_price_text = full_price.text
                    actual_price = parse_price(full_price_text)
                    common_price = product.find('p', class_='price-common').find('span')
                    if common_price:
                        current_data['sale'] = True
                        price = parse_price(common_price.text)
                        current_data['price'] = price
                        current_data['fullPrice'] = actual_price
                    else:
                        current_data['sale'] = False
                        current_data['fullPrice'] = actual_price
                        current_data['price'] = actual_price

                    result.append(current_data)
                nav = row_cols_part.find('nav', role='navigatoin')
                next_page = nav.find('a', class_='btn btn-silver btn-icon-after btn-icon-after-pag btn-s btn-change-page ajax')
                if next_page:
                    url = clean(next_page['href'])
                    print(url)
                else:
                    break
                time.sleep(1.5)
            except Exception as e:
                print(e)
        return result


"""
title               Название книги
author              Автор  
price               Текущая цена 
(CZK)original_price Цена до скидки (если есть)
discount_percent    Процент скидки
availability        В наличии / Нет в наличии
rating              Рейтинг (если есть)
url                 Ссылка на книгу
category            Категория
==================================================
ID
sale
{'title':_,'author':_ 'price':_,'original_price':_,'discount_percent':_,'availability':_,'rating':_, 'url':_, 'category':_}
--------------------------------------------------
outputs:
 
CSV файл — для Excel анализа
JSON файл — структурированные данные
Краткий отчёт — топ-10 скидок, средняя цена по категориям
"""
