from datetime import datetime


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if len(value) == 4 and value.isdigit():  # YYYY
        return value + "-01-01"
    if len(value) == 7:  # YYYY-MM
        return value + "-01"
    if len(value) == 10:  # YYYY-MM-DD
        return value
    return None