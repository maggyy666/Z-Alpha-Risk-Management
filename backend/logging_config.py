"""Central logging configuration.

Called once at process startup (FastAPI lifespan, setup_database main).
Level is taken from `settings.log_level` (default INFO). All library
loggers inherit from root; uvicorn/sqlalchemy levels are nudged down so
the app's own logs stay readable.
"""

from __future__ import annotations

import logging
import sys

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str | None = None) -> None:
    """Configure root logger once. Idempotent -- safe to call multiple times.
    `level` overrides settings.log_level if provided (used by CLI tooling
    that wants to bump verbosity for a single run)."""
    if level is None:
        from config import settings
        level = settings.log_level
    lvl = level.upper()

    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)
    root.setLevel(lvl)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
