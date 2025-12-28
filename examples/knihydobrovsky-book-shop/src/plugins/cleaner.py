def parse_price(text: str) -> float:
    """'149 Kč' -> 149.0"""
    return float(text.replace('Kč', '').replace(' ', '').strip())