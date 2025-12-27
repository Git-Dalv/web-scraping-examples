from bs4 import BeautifulSoup
from pathlib import Path
from scr.plugins.cleaner import clean
from datetime import datetime, date, timedelta

import asyncio
import re

TIME_UNITS = {
    'den': 'day',
    'dny': 'days',
    'dnů': 'days',
    'hodina': 'hour',
    'hodiny': 'hours',
    'hodin': 'hours',
    'týden': 'week',
    'týdny': 'weeks',
    'týdnů': 'weeks'
}

DATE = {
    'leden': 1, 'ledna': 1,
    'únor': 2, 'února': 2,
    'březen': 3, 'března': 3,
    'duben': 4, 'dubna': 4,
    'květen': 5, 'května': 5,
    'červen': 6, 'června': 6,
    'červenec': 7, 'července': 7,
    'srpen': 8, 'srpna': 8,
    'září': 9,
    'říjen': 10, 'října': 10,
    'listopad': 11, 'listopadu': 11,
    'prosinec': 12, 'prosince': 12,
}

SELECTORS = [
    "button:has-text('Přijmout všechny')",
    "button:has-text('Přijmout vše')",
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Souhlasím')",
    "button:has-text('OK')",
    "[data-testid='cookie-accept']",
    "#onetrust-accept-btn-handler",
    ".cookie-accept",
]

MAIN_SELECTORS = [
    'main',
    '[role="main"]',
    'article',
    '.job-description',
    '.job-detail',
    '.job-content',
    '[class*="JobDetail"]',
    '[class*="job-detail"]',
    '[class*="jobDetail"]',
    '[class*="Description"]',
    '[class*="description"]',
    '[class*="Content"]',
    '[class*="content"]',
    '[id*="job"]',
    '[id*="content"]',
    '[id*="main"]',
    '.main',
    '#main',
    '#content',
]
GARBAGE_SELECTORS = [
    'header',
    'footer',
    'nav',
    'script',
    'style',
    'aside',
    '[class*="cookie"]',
    '[class*="banner"]',
    '[class*="modal"]',
    '[class*="Modal"]',
    '[class*="popup"]',
    '[class*="Popup"]',
    '[class*="dialog"]',
    '[class*="Dialog"]',
    '[class*="overlay"]',
    '[class*="Overlay"]',
    '[role="dialog"]',
    '[aria-modal="true"]',
    '[class*="share"]',
    '[class*="Share"]',
    '[class*="social"]',
    '[class*="Social"]',
]

GARBAGE_PATTERNS = [
    "Poslat nabídku na e-mail",
    "Poslat na e-mail",
    "E-mail příjemce",
    "Zadejte správný formát",
    "Za účelem zaslání pracovní nabídky",
    "Alma Career",
]


def is_garbage_content(text: str) -> bool:
    if len(text) < 200:
        return True

    for pattern in GARBAGE_PATTERNS:
        if text.startswith(pattern) or pattern in text[:300]:
            return True

    return False


def extract_main_content(soup: BeautifulSoup) -> str:
    for selector in GARBAGE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    for selector in MAIN_SELECTORS:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            if len(text) > 200 and not is_garbage_content(text):
                return clean(text)

    body = soup.find('body')
    if body:
        text = clean(body.get_text(strip=True))
        if not is_garbage_content(text):
            return text

    return ""


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_deadline(text):
    pattern = r'(\d+)\s*(' + '|'.join(TIME_UNITS.keys()) + r')'
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    number = int(match.group(1))
    unit_czech = match.group(2).lower()
    unit_english = TIME_UNITS.get(unit_czech)

    now = datetime.now()

    if 'day' in unit_english:
        end_date = now + timedelta(days=number)
    elif 'hour' in unit_english:
        end_date = now + timedelta(hours=number)
    elif 'week' in unit_english:
        end_date = now + timedelta(weeks=number)
    else:
        end_date = now

    return {'Ending_soon': end_date.isoformat()}


def current_date(text_date: str):
    text = text_date.strip().lower()
    today = date.today()

    if "dnes" in text.lower():
        return today.isoformat()

    if "včera" in text.lower():
        return (today - timedelta(days=1)).isoformat()

    if 'končí' in text.lower():
        return get_deadline(text)

    try:
        day_part, month_name = text.replace(".", "").split()
        day = int(day_part)
        month = DATE[month_name]
        result = date(today.year, month, day)

        if result > today:
            result = date(today.year - 1, month, day)

        return result
    except Exception:
        return None


async def accept_cookies(page, session):
    for selector in SELECTORS:
        try:
            button = await page.query_selector(selector)
            if button:
                await session.human_click(page, selector)
                await session.human_delay()
                return True
        except:
            continue

    return False
