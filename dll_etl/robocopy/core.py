"""Core functions for robocopy.

This tool enables the migration of synchronization scripts away from
slow python-level file metadata polling and onto a fast, robust OS-level
execution via Robocopy.
"""

# %%
####################
# Import Statement #
####################
import subprocess
from pathlib import Path

from dll_etl.reusable import NothingToLoadError, logger

log = logger.bind(logger_name="dll_etl>robocopy")


###########
# CLASSES #
###########
class RobocopyError(Exception):
    """Exception raised when robocopy returns a failing exit code."""


ROBOCOPY_EXIT_CODES = {
    0: "No files copied",
    1: "Files copied successfully",
    2: "Extra files detected",
    3: "Files copied, extra files detected",
    4: "Mismatched files detected",
    5: "Files copied, mismatched files detected",
    6: "Extra files and mismatched files detected",
    7: "Files copied, extra & mismatched files detected",
    8: "Copy errors occurred (e.g. retry limit exceeded)",
    16: "Severe error (e.g. fatal filesystem error, insufficient permissions)",
}


def _handle_rc(
    src: Path,
    rc: int,
    stdout: str,
    stderr: str,
) -> int:
    """Interpret Robocopy bitwise exit codes."""
    # 0x10 : 16: Serious error (usage error, access rights, path not found).
    if rc >= 16:
        reason = "Serious error (path not found, access rights, or usage error)"
        err_msg = f"{src.stem} - Robocopy failed with exit code {rc} ({reason})"
        log.error(f"{err_msg}:\n{stderr or stdout}")
        raise RobocopyError(err_msg)

    # 0x08 : 8 : Some files failed to copy.
    if rc >= 8:
        reason = "Some files failed to copy (retry limit exceeded?)"
        err_msg = f"Robocopy completion with errors (code {rc}): {reason}"
        log.error(f"{src.stem} - {err_msg}:\n{stderr or stdout}")
        raise RobocopyError(err_msg)

    # 0x00 : 0 : No files copied.
    if rc == 0:
        raise NothingToLoadError(f"{src.stem} - No files were copied.")

    # 0x01, 0x02, 0x04 bits are success flavors
    success_reasons = []
    if rc & 1:
        success_reasons.append(f"{src.stem} - Files copied")
    if rc & 2:
        success_reasons.append(f"{src.stem} - Extra files detected")
    if rc & 4:
        success_reasons.append(f"{src.stem} - Mismatched files detected")

    log.debug(f"{src.stem} - Robocopy success (code {rc}): {', '.join(success_reasons)}")
    return rc


#############
# FUNCTIONS #
#############
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
) -> int:
    """Run robocopy to synchronize files from src to dst.

    Parameters
    ----------
    src : Path | str
        Source directory
    dst : Path | str
        Destination directory
    file_filter : str
        File filter to apply, defaults to "*.*"
    exclude_files : list[str] | None
        List of specific file names to exclude (e.g., from `to_skip`)
    threads : int
        Number of concurrent threads (Robocopy /MT flag). Max 128.
    exclude_older : bool
        If True, adds /XO flag to exclude older equivalent files.
    restartable : bool
        If True, adds /Z flag to copy files in restartable mode (survives network drops).
    fat_file_times : bool
        If True, adds /FFT flag. This assumes FAT file times (2-second granularity).
        Useful for network shares where timestamp precision can jitter.
    extra_flags : list[str] | None
        Any additional standard robocopy flags to include.

    Returns
    -------
    int
        The robocopy successful exit code (between 0 and 7).

    Raises
    ------
    NothingToLoadError
        If no files were moved (exit code 0).
    RobocopyError
        If robocopy encounters a severe failure (exit code >= 8).
    """

    if not Path(src).exists():
        raise NothingToLoadError(f"Source directory {src} does not exist.")

    # --- Variables ---
    cmd = [
        "robocopy",
        str(src),
        str(dst),
        file_filter,
        f"/MT:{threads}",  # Multithreaded
        "/NP",  # No Progress - don't pollute logs with %
        "/NDL",  # No Directory List - don't log directory names
        "/NJH",  # No Job Header
        "/NJS",  # No Job Summary
        "/BYTES",  # Print sizes in bytes
        "/W:3",  # Wait time between retries
        "/R:3",  # Number of retries on failed copies
    ]

    # --- Script ---
    # Append critical flaggs
    if exclude_older:
        cmd.append("/XO")

    if restartable:
        cmd.append("/Z")

    if fat_file_times:
        cmd.append("/FFT")

    # Append any manually specified extra flags
    if extra_flags:
        cmd.extend(extra_flags)

    # Exclude files last, to correctly build the /XF list
    if exclude_files:
        cmd.append("/XF")
        cmd.extend(exclude_files)

    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
        errors="replace",
    )
    _handle_rc(
        src=Path(src),
        rc=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    for line in lines:
        log.info(f"[Robocopy] {line}")

    return result.returncode
