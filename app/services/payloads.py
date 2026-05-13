from typing import Any


def to_db_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            normalized[key] = value
        elif hasattr(value, "unicode_string"):
            normalized[key] = str(value)
        else:
            normalized[key] = value
    return normalized
