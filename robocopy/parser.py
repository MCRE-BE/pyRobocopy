"""Output parsing logic for Robocopy stdout streams."""

# %%
####################
# Import Statement #
####################
import re
from pathlib import Path

from .config import RobocopyConfig
from .types import FileResult, RobocopyStatus

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

    _error_re = re.compile(r"ERROR (\d+) \(0x[0-9A-Fa-f]+\)")
    _retry_re = re.compile(r"Waiting (\d+) seconds\.\.\. Retrying\.\.\.")

    # Status keyword mapping (lowercase for case-insensitive matching)
    _STATUS_MAP = {  # noqa: RUF012
        "new file": RobocopyStatus.NEW_FILE,
        "new dir": RobocopyStatus.NEW_DIR,
        "newer": RobocopyStatus.NEWER,
        "older": RobocopyStatus.OLDER,
        "same": RobocopyStatus.SAME,
        "*same*": RobocopyStatus.SAME,
        "extra file": RobocopyStatus.EXTRA_FILE,
        "*extra file": RobocopyStatus.EXTRA_FILE,
        "extra dir": RobocopyStatus.EXTRA_DIR,
        "*extra dir": RobocopyStatus.EXTRA_DIR,
        "mismatched": RobocopyStatus.MISMATCH,
        "mismatch": RobocopyStatus.MISMATCH,
        "*mismatch*": RobocopyStatus.MISMATCH,
        "modified": RobocopyStatus.MODIFIED,
        "tweaked": RobocopyStatus.TWEAKED,
        "lonely": RobocopyStatus.LONELY,
    }

    def __init__(self, config: RobocopyConfig):
        self.config = config
        self.stats_found = False

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
        line_stripped = line.strip()
        if not line_stripped:
            return None

        # Check for error codes
        if "ERROR" in line_stripped and (match := self._error_re.search(line_stripped)):
            err_code = match.group(1)
            category = WINDOWS_ERROR_CODES.get(
                err_code,
                "Unknown Error",
            )
            return f"Error {err_code} ({category}): {line_stripped}"

        # Check for retry/waiting
        if "Waiting" in line_stripped and (match := self._retry_re.search(line_stripped)):
            return f"RETRY_WAIT:{match.group(1)}"

        # Summary Header marker
        if "Total    Copied   Skipped" in line_stripped:
            self.stats_found = True
            return "SUMMARY_START"

        # Check for file status (case-insensitive)
        line_lower = line_stripped.lower()
        for kw, status in self._STATUS_MAP.items():
            if kw in line_lower:
                parts = line_stripped.split()
                if parts:
                    # In some cases, the last part might be '100%' if it's on the same line
                    path_idx = -1
                    if parts[-1].endswith("%"):
                        path_idx = -2

                    try:
                        res = FileResult(
                            status=status,
                            source_path=Path(parts[path_idx]),
                        )
                        return res  # noqa: TRY300
                    except (IndexError, ValueError):
                        continue

        return line_stripped
