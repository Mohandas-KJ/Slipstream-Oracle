"""sliplog package - lightweight logging helpers for SlipStream-Oracle

Provides a small helper to get a configured logger for package modules.
"""
from __future__ import annotations

import logging
from typing import Optional

__all__ = ["get_logger", "__version__"]

__version__ = "0.1.0"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger configured for library usage.

    If no handlers are attached by the application, a NullHandler is added
    so library logging calls don't print to the root logger by default.
    ``name`` defaults to the package name when not provided.
    """
    if name is None:
        name = __package__ or "sliplog"

    logger = logging.getLogger(name)

    # If the application hasn't attached handlers to this logger or its
    # ancestors, ensure we don't emit to the root logger by default.
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger
