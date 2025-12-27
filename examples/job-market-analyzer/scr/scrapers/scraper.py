from scr.plugins.helper_functions import get_project_root, current_date, accept_cookies
from scr.plugins.cleaner import clean

from phantom_persona import PhantomPersona
from phantom_persona.config import ConfigLoader

from bs4 import BeautifulSoup
from pathlib import Path
from contextlib import asynccontextmanager

import asyncio

WAIT_TIME = 1.5


def create_client() -> PhantomPersona:
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "configs" / "config.yaml"
    config = ConfigLoader.load(config_path)
    return PhantomPersona(config=config)


# ==================================================================================================
#                                 Main Pipeline
# ==================================================================================================

project_root = get_project_root()
reports_dir = project_root / 'error_dir'
reports_dir.mkdir(exist_ok=True)


async def get_jobs_page(session, job_title: str, location: str):
    page = await session.new_page()
    await page.goto('https://jobs.cz')
    await page.wait_for_load_state('networkidle')

    await accept_cookies(page, session)
    await session.human_delay()

    await session.human_type(page, '#interest-select', job_title)
    await page.keyboard.press('Enter')
    await session.human_delay()

    await session.human_type(page, '#locality-select', location)
    await session.human_delay()
    await page.keyboard.press('Enter')

    await session.human_click(page, 'button[type="submit"]')
    await session.human_delay()

    return page


async def scrape_jobs(page, session):
    urls = []
    page_number = 1
    while True:
        html = await page.content()
        bs = BeautifulSoup(html, 'html.parser')
        jobs_part = bs.find_all('article', class_='SearchResultCard')
        print(f'Jobs found {len(jobs_part)} on page {page_number}')
        for job in jobs_part:
            try:
                header = job.find('header')
                if not header:
                    print('No header')

                str_date = header.find('div', attrs={'data-test-ad-status': True}).text
                cur_date = current_date(str_date)

                deadline = False
                if isinstance(cur_date, dict):
                    deadline = True
                    cur_date = cur_date['Ending_soon']

                h2 = header.find('h2', attrs={'data-test-ad-title': True})
                a = h2.find('a')
                job_name = a.text
                source_id = a["data-jobad-id"]

                if job_name: job_name = clean(job_name)

                job_url = h2.find('a')['href']
                footer = job.find('footer')

                company = footer.find('span', translate=True).text
                if company: company = clean(company)

                location = footer.find('li', attrs={"data-test": "serp-locality"}).text
                if location: location = clean(location)

                urls.append({
                    'source_id': source_id,
                    'deadline': deadline,
                    'title': job_name,
                    'location': location,
                    'company': company,
                    'date': cur_date,
                    'url': job_url
                })

                print(
                    f'|\tID:{source_id}\t|\n|Title: {job_name}| |Location: {location}| |Company: {company}| |Deadline: {deadline}| |date: {cur_date}| |url: {job_url}|')
            except Exception as e:
                report = f'{reports_dir}/scrape_jobs_page_{page_number}.png'
                await page.screenshot(path=report, full_page=True)
                print(f'Error: {e}')
                continue

        page_number += 1

        await asyncio.sleep(WAIT_TIME)

        selector = f"a[aria-label='Přejít na stránku {page_number}']"
        link = await page.query_selector(selector)
        if link:
            await session.human_click(page, selector)
            await session.human_delay()
            await page.wait_for_load_state('networkidle')
        else:
            print(f'\t{len(urls)} jobs found\t')
            print('Next page not found')
            break

    return urls