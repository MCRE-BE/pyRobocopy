"""Public API for the Robocopy synchronization tool."""

__all__ = [
    "robocopy",
    "NothingToLoadError",
    "RobocopyError",
    "RobocopyConfig",
    "RobocopyRunner",
    "RobocopyResult",
    "RobocopyStatistics",
    "FileResult",
    "CopyOptions",
    "SelectionOptions",
    "LoggingOptions",
    "RobocopyStatus",
    "StatRow",
    "RobocopyStatus",
    "StatRow",
    "RobocopyParser",
]

# %%
####################
# Import Statement #
####################
import logging
from pathlib import Path

from .error import NothingToLoadError, RobocopyError

from .config import (
    CopyOptions,
    LoggingOptions,
    RobocopyConfig,
    SelectionOptions,
)
from .parser import RobocopyParser
from .runner import RobocopyRunner
from .types import (
    FileResult,
    RobocopyResult,
    RobocopyStatistics,
    RobocopyStatus,
    StatRow,
)


def robocopy(
    src: Path | str,
    dst: Path | str,
    file_filter: str = "*.*",
    exclude_files: list[str] | None = None,
    threads: int = 16,
    exclude_older: bool = True,
    restartable: bool = False,
    fat_file_times: bool = True,
    extra_flags: list[str] | None = None,
    progress: bool = False,
    smart_progress: bool = False,
    logger: logging.Logger | None = None,
) -> int:
    """Functional wrapper for the OO Robocopy system.

    Maintains backward compatibility for simple synchronization tasks.

    Parameters
    ----------
    src : Path | str
        Source directory.
    dst : Path | str
        Destination directory.
    file_filter : str
        Pattern for files to copy.
    exclude_files : list[str], optional
        Filenames or patterns to exclude.
    threads : int
        Number of concurrent threads.
    exclude_older : bool
        If True, skips source files that aren't newer than target.
    restartable : bool
        If True, uses restartable mode.
    fat_file_times : bool
        If True, assumes 2-second timestamp resolution.
    extra_flags : list[str], optional
        Additional CLI flags.
    progress : bool
        Enables progress display.
    smart_progress : bool
        Enables discovery-based percentage progress bar.
    logger : logging.Logger, optional
        Custom logger to use for output.

    Returns
    -------
    int
        Final Robocopy exit code.
    """
    config = RobocopyConfig(
        source=Path(src),
        destination=Path(dst),
        files=file_filter,
        copy=CopyOptions(
            multi_threaded=threads,
            restartable=restartable,
            fat_file_times=fat_file_times,
        ),
        selection=SelectionOptions(
            exclude_older=exclude_older,
            exclude_files=exclude_files or [],
            extra_flags=extra_flags or [],
        ),
    )

    runner = RobocopyRunner(
        config=config,
        logger=logger,
    )
    result = runner.run(
        smart_progress=(progress or smart_progress),
    )

    if result.exit_code == 0 and result.stats.files.total == 0:
        raise NothingToLoadError(f"No files found to copy in {src}")

    return result.exit_code
