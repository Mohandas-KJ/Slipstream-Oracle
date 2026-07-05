
"""Generals package

Provide shared utilities and common definitions for SlipStream-Oracle.

Keep this file minimal to avoid side-effects on import.
"""

__all__ = [
	"__version__",
]

__version__ = "0.1.0"

# Expose optionally used utilities here to make imports convenient.
# from .utils import some_helper  # noqa: F401


# Package-level convenience: simple repr
def __repr__():
	return f"<Generals package version={__version__}>"


