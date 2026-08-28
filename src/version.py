"""Single source of truth for the GTEM version.

Every PDF report, CSV header and log line is stamped with ``VERSION_STAMP`` so
that any result can be traced back to the code that produced it. Previously no
output recorded which version generated it.

Bump ``__version__`` here and nowhere else.
"""

from __future__ import annotations

__version__ = "1.0.0"

MODEL_NAME = "GTEM"
MODEL_LONG_NAME = "Global Tsunami Evacuation Model"

#: Engine this release is tested against. Reported by check_environment.py.
TESTED_NETLOGO = "7.0.4"
TESTED_JAVA = "17.0.2 (bundled with NetLogo 7.0.4)"

#: Goes into figures, CSV headers, PDF footers and warnings.log.
VERSION_STAMP = f"{MODEL_NAME} {__version__}"


def provenance_line() -> str:
    """One-line provenance string for embedding in any output artefact."""
    return (
        f"{MODEL_LONG_NAME} ({MODEL_NAME}) {__version__} | "
        f"NetLogo {TESTED_NETLOGO}"
    )
