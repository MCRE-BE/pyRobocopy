"""Data structures and types for Robocopy operations."""

# %%
####################
# Import Statement #
####################
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import RobocopyConfig


###########
# CLASSES #
###########
class RobocopyStatus(Enum):
    """Categorization of individual file/folder outcomes.

    Attributes
    ----------
    NEW_FILE : str
        File exists in source but not in destination.
    NEWER : str
        Source file is newer than destination file.
    OLDER : str
        Source file is older than destination file.
    SAME : str
        Source and destination files are identical.
    EXTRA : str
        File exists in destination but not in source.
    MISMATCH : str
        Source and destination file sizes differ.
    TWEAKED : str
        Attributes differ but timestamps/sizes match.
    FAILED : str
        File failed to process.
    UNKNOWN : str
        Status could not be determined.
    """

    NEW_FILE = "New File"
    NEW_DIR = "New Dir"
    NEWER = "Newer"
    OLDER = "Older"
    SAME = "*SAME*"
    EXTRA_FILE = "*EXTRA File"
    EXTRA_DIR = "*EXTRA Dir"
    MISMATCH = "*MISMATCH*"
    MODIFIED = "Modified"
    TWEAKED = "Tweaked"
    FAILED = "FAILED"
    LONELY = "Lonely"
    UNKNOWN = "Unknown"

    @property
    def counts_towards_total(self) -> bool:
        """Indicates if this status represents a source file processed.

        Excludes directories and 'Extra' files (destination only).
        """
        val = str(self.value)
        if "Dir" in val:
            return False
        if "EXTRA" in val:
            return False
        return val != "Unknown"


@dataclass
class StatRow:
    """Individual row of statistics from the robocopy summary table.

    Attributes
    ----------
    total : int
        Total item count.
    copied : int
        Number of items successfully copied.
    skipped : int
        Number of items skipped (identical or excluded).
    mismatched : int
        Number of items with differing attributes or sizes.
    failed : int
        Number of items that failed to process.
    extras : int
        Number of items found in destination but not in source.
    """

    total: int = 0
    copied: int = 0
    skipped: int = 0
    mismatched: int = 0
    failed: int = 0
    extras: int = 0


@dataclass
class RobocopyStatistics:
    """Consolidated statistics from a robocopy execution.

    Attributes
    ----------
    dirs : StatRow
        Statistics for directories.
    files : StatRow
        Statistics for files.
    bytes : StatRow
        Statistics for data volume in bytes.
    """

    dirs: StatRow = field(default_factory=StatRow)
    files: StatRow = field(default_factory=StatRow)
    bytes: StatRow = field(default_factory=StatRow)


@dataclass
class FileResult:
    """Record of an individual file's copy outcome.

    Attributes
    ----------
    status : RobocopyStatus
        The outcome category of the file process.
    source_path : Path
        The absolute or relative path to the source file.
    size : int, optional
        Size of the file in bytes.
    timestamp : datetime, optional
        Source file's modification timestamp.
    error_msg : str, optional
        Human-readable error description if status is FAILED.
    """

    status: RobocopyStatus
    source_path: Path
    size: int | None = None
    timestamp: datetime | None = None
    error_msg: str | None = None


@dataclass
class RobocopyResult:
    """The outcome of a robocopy execution.

    Attributes
    ----------
    config : Any
        The configuration used for this run. (Typed as Any to avoid circularity).
    exit_code : int
        The raw bitwise exit code from Robocopy.
    stats : RobocopyStatistics
        Parsed summary table statistics.
    files : list[FileResult]
        Detailed list of file outcomes (if configured).
    errors : list[str]
        List of raw ERROR lines found in the output.
    """

    config: "RobocopyConfig"  # Forward reference
    exit_code: int
    stats: RobocopyStatistics = field(default_factory=RobocopyStatistics)
    files: list[FileResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Determines if the operation was conceptually successful.

        Returns
        -------
        bool
            True if exit_code < 8 (Catastrophic errors start at 8).
        """
        return self.exit_code < 8
