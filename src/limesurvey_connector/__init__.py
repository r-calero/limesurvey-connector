"""LimeSurvey connector: survey contract, data dictionaries and RemoteControl 2 access."""

import logging
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("limesurvey-connector")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

from survey_structure import SURVEY_STRUCTURE_VERSION

# Library logging stays silent unless the application configures it.
logging.getLogger(__name__).addHandler(logging.NullHandler())

# npm packages whose behavior this implementation reproduces.
REFERENCE_IMPLEMENTATIONS = {
    "survey-structure": "2.1.0",
    "survey-data-dictionary": "2.1.0",
}

__all__ = [
    "REFERENCE_IMPLEMENTATIONS",
    "SURVEY_STRUCTURE_VERSION",
    "__version__",
]
