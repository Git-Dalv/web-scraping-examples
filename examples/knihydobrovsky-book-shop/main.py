from src.scraper.scraper import scrape
from src.analysis.analysis import analyse_it

if __name__ == '__main__':
    urls_to_scrape = ['/slevy', '/bestsellery/knihy', '/knihy?type=newitem']
    data = []
    for url in urls_to_scrape:
        books = scrape(url)
        data.extend(books)
    analyse_it(data)

