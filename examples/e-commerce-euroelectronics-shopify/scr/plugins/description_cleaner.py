import re
import html


def parse_product_description(html_text: str):
    if not html_text:
        return '', {}

    # 1. Decode HTML entities
    text = html.unescape(html_text)

    # 2. Replace NBSP with regular space
    text = text.replace('\xa0', ' ')
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'NBSP', ' ', text, flags=re.IGNORECASE)  # Text "NBSP"

    # 3. Replace <br> with newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # 4. Replace <li> with newlines
    text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)

    # 5. Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # 6. Remove special characters
    text = re.sub(r'[^\w\s.,;:!?\'\"()\-\n%€$£°+/]', '', text)

    # 7. Fix multiple spaces/newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = text.strip()

    # 8. Split description and specifications
    match = re.search(r'\n-', text)

    if match:
        description = text[:match.start()].strip()
        specs_text = text[match.start():].strip()

        specifications = {}
        for line in specs_text.split('\n'):
            line = line.strip().lstrip('- ')
            if ':' in line:
                key, value = line.split(':', 1)
                specifications[key.strip()] = value.strip()
            elif line:
                specifications[line] = ''
    else:
        description = text
        specifications = {}

    return description, specifications