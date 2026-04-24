"""Central logging configuration.

Called once at process startup (FastAPI lifespan, setup_database main).
Level is controlled by the LOG_LEVEL env var (default INFO). All library
loggers inherit from root; uvicorn/sqlalchemy levels are nudged down so
the app's own logs stay readable.
"""

from __future__ import annotations

import logging
import os
import sys

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str | None = None) -> None:
    """Configure root logger once. Idempotent -- safe to call multiple times."""
    lvl = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()

    root = logging.getLogger()
    # Replace any pre-existing handlers (uvicorn may have added its own)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)
    root.setLevel(lvl)

    # Quiet down chatty third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
