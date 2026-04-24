"""JSON serialization helpers.

FastAPI's default JSON encoder rejects NaN/Inf floats (they are not valid JSON).
clean_json_values walks a nested structure and replaces them with 0.0 so that
responses remain valid JSON for the frontend. Applied once at the boundary;
analytics code does not need to worry about it internally.
"""

from __future__ import annotations

import math
from typing import Any


def clean_json_values(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: clean_json_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json_values(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(clean_json_values(v) for v in obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
    return obj
