from __future__ import annotations

import json
import re
from typing import Any, List

class JSONParsingError(ValueError):
    pass


def extract_json_array(text: str) -> Any:
    """Extract the first JSON array from the text and return the parsed object."""
    text = text.strip()
    if not text:
        raise JSONParsingError("Empty response when JSON array expected.")

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Search for JSON array substring
    match = re.search(r"(\[\s*{.*}\s*\])", text, re.DOTALL)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise JSONParsingError(f"Failed to parse JSON array: {exc}") from exc

    raise JSONParsingError("No JSON array found in response.")


def ensure_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value]
    if isinstance(value, str):
        return [value.strip()]
    raise JSONParsingError("Value cannot be coerced into list of strings.")
