"""Output parsing logic for Robocopy stdout streams."""

# %%
####################
# Import Statement #
####################
import re

from .config import RobocopyConfig
from .types import FileResult

#############
# VARIABLES #
#############
WINDOWS_ERROR_CODES = {
    "2": "File Not Found",
    "3": "Path Not Found",
    "5": "Access Denied",
    "32": "File In Use (Busy)",
    "64": "Network Name Deleted",
    "121": "Network Timeout",
}


###########
# CLASSES #
###########
class RobocopyParser:
    """Handles parsing of raw robocopy stdout stream.

    Parameters
    ----------
    config : RobocopyConfig
        The configuration context for parsing variables.
    """

    def __init__(self, config: RobocopyConfig):
        self.config = config
        self.stats_found = False
        self.error_re = re.compile(r"ERROR (\d+) \(0x[0-9A-Fa-f]+\)")

    def parse_line(self, line: str) -> FileResult | str | None:
        """Analyze a single line and extract meaning.

        Parameters
        ----------
        line : str
            Raw output line from robocopy.

        Returns
        -------
        FileResult | str | None
            A categorized result, error string, or None.
        """
        line = line.strip()
        if not line:
            return None

        # Check for error codes
        if "ERROR" in line and (match := self.error_re.search(line)):
            err_code = match.group(1)
            category = WINDOWS_ERROR_CODES.get(
                err_code,
                "Unknown Error",
            )
            return f"Error {err_code} ({category}): {line}"

        # Summary Header marker
        if "Total    Copied   Skipped" in line:
            self.stats_found = True
            return "SUMMARY_START"

        return line
