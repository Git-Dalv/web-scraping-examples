from text_cleaner import clean
import re
import json


def parse_product_info(raw: str) -> dict:
    fixed = re.sub(
        r'"(\w+)"\s*:\s*([^",\[\]{}][^"\n]*?)(?=,\s*"\w+"\s*:|,?\s*})',
        r'"\1": "\2"',
        raw
    )
    json_data = json.loads(fixed)
    new_dict = {k: re.sub(r"[,]", "/", clean(v)) for k, v in json_data.items()}

    return new_dict

