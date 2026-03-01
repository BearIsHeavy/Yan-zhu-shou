# app/utils/helpers.py
from typing import Dict, Any


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback value."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default