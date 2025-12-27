import re
import html
from text_cleaner import TextCleaner


def price_cleaner(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.,-]', '', price_str)

    if ',' in cleaned and '.' in cleaned:
        last_comma = cleaned.rfind(',')
        last_dot = cleaned.rfind('.')

        if last_dot > last_comma:
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        if cleaned.rfind(',') > len(cleaned) - 4:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def m_cleaner(text_with_price: str) -> float:
    match = re.search(r'€([\d.,]+)', text_with_price)
    if match:
        price_str = match.group(1)
        price = float(price_str.replace(',', '.'))
        return price
    else:
        return 0.0


def clean_text(text) -> str:
    """Universal text cleaner for product names, vendors, etc."""
    cleaner = TextCleaner(
        remove_quotes=False,  # Keep quotes
        preserve_newlines=False,  # Keep line breaks
        lowercase=False,  # Convert to lowercase
        max_length=300,  # Truncate long text
    )
    new_text = cleaner.clean(text)

    return new_text
