"""Configuration models for Robocopy executions."""

# %%
####################
# Import Statement #
####################
import shlex
from dataclasses import dataclass, field
from pathlib import Path

# Mapping of simple boolean flags to their configuration attribute paths
_BOOLEAN_FLAGS = {
    "/S": ("copy", "subdirs"),
    "/E": ("copy", "empty_subdirs"),
    "/Z": ("copy", "restartable"),
    "/B": ("copy", "backup_mode"),
    "/FFT": ("copy", "fat_file_times"),
    "/PURGE": ("copy", "purge"),
    "/XO": ("selection", "exclude_older"),
    "/XX": ("selection", "exclude_extra"),
    "/V": ("logging", "verbose"),
    "/NFL": ("logging", "no_file_list"),
    "/NDL": ("logging", "no_dir_list"),
}

# Mapping of flags with prefixes (like /MT:8) to their config paths and types
_PREFIX_FLAGS = {
    "/MT:": (("copy", "multi_threaded"), int),
    "/COPY:": (("copy", "copy_flags"), str),
    "/DCOPY:": (("copy", "dir_copy_flags"), str),
    "/R:": (("retry_count",), int),
    "/W:": (("retry_wait",), int),
}


###########
# CLASSES #
###########
@dataclass
class CopyOptions:
    """Robocopy Copy behavior options (/S, /E, /Z, etc.).

    Attributes
    ----------
    subdirs : bool
        If True, copies subdirectories (excluding empty ones) [/S].
    empty_subdirs : bool
        If True, copies all subdirectories including empty ones [/E].
    restartable : bool
        If True, copies files in restartable mode (survives network drops) [/Z].
    backup_mode : bool
        If True, uses Backup mode (overrides many permissions) [/B].
    multi_threaded : int
        Number of concurrent threads. Default is 8 [/MT:n].
    fat_file_times : bool
        If True, assumes 2-second timestamp granularity [/FFT].
    copy_flags : str
        What to copy (D:Data, A:Attributes, T:Timestamps, etc.) [/COPY:flags].
    dir_copy_flags : str
        What to copy for directories [/DCOPY:flags].
    purge : bool
        If True, deletes destination files/dirs that no longer exist in source [/PURGE].
    mirror : bool
        If True, mirrors the source to destination (Equivalent to /E /PURGE) [/MIR].
    """

    subdirs: bool = False
    empty_subdirs: bool = False
    restartable: bool = False
    backup_mode: bool = False
    multi_threaded: int = 8
    fat_file_times: bool = True
    copy_flags: str = "DAT"
    dir_copy_flags: str = "DA"
    purge: bool = False
    mirror: bool = False


@dataclass
class SelectionOptions:
    """Robocopy File selection filters (/XO, /XF, etc.).

    Attributes
    ----------
    exclude_older : bool
        If True, excludes older source files than destination equivalents [/XO].
    exclude_extra : bool
        If True, excludes files in destination not present in source [/XX].
    exclude_files : list[str]
        Patterns or filenames to specifically skip [/XF].
    exclude_dirs : list[str]
        Directory patterns or paths to specifically skip [/XD].
    include_archive_only : bool
        If True, only copies files with the Archive attribute set [/A].
    reset_archive : bool
        If True, resets the Archive attribute after copying [/M].
    extra_flags : list[str]
        Any additional selection or copy flags not covered above.
    """

    exclude_older: bool = True
    exclude_extra: bool = False
    exclude_files: list[str] = field(default_factory=list)
    exclude_dirs: list[str] = field(default_factory=list)
    include_archive_only: bool = False
    reset_archive: bool = False
    extra_flags: list[str] = field(default_factory=list)


@dataclass
class LoggingOptions:
    """Robocopy logging and output display options (/V, /NFL, etc.).

    Attributes
    ----------
    verbose : bool
        If True, produces verbose output showing skipped files [/V].
    no_file_list : bool
        If True, does not log individual filenames [/NFL].
    no_dir_list : bool
        If True, does not log directory names [/NDL].
    show_timestamps : bool
        If True, includes source timestamps in output [/TS].
    full_pathnames : bool
        If True, logs full pathnames of files [/FP].
    bytes_as_integers : bool
        If True, logs sizes as bytes rather than K/M/G [/BYTES].
    no_job_header : bool
        If True, suppresses the Robocopy job header [/NJH].
    no_job_summary : bool
        If True, suppresses the Robocopy job summary [/NJS].
    tee : bool
        If True, outputs to both console and log file [/TEE].
    """

    verbose: bool = False
    no_file_list: bool = False
    no_dir_list: bool = True
    show_timestamps: bool = False
    full_pathnames: bool = False
    bytes_as_integers: bool = True
    no_job_header: bool = False
    no_job_summary: bool = False
    tee: bool = False


@dataclass
class RobocopyConfig:
    """Full configuration set for a robocopy execution.

    Contains sub-configurations for copying, selection, and logging.

    Attributes
    ----------
    source : Path
        Source directory path.
    destination : Path
        Destination directory path.
    files : str
        File filter pattern (default "*.*").
    copy : CopyOptions
        Configuration for copy behavior.
    selection : SelectionOptions
        Configuration for file selection.
    logging : LoggingOptions
        Configuration for output and logging.
    retry_count : int
        Number of retries on failed copies [/R:n].
    retry_wait : int
        Seconds to wait between retries [/W:n].
    """

    source: Path
    destination: Path
    files: str = "*.*"
    copy: CopyOptions = field(default_factory=CopyOptions)
    selection: SelectionOptions = field(default_factory=SelectionOptions)
    logging: LoggingOptions = field(default_factory=LoggingOptions)
    retry_count: int = 3
    retry_wait: int = 3

    @classmethod
    def from_command_line(cls, cmd_string: str) -> "RobocopyConfig":
        r"""Parse a raw robocopy command string into a RobocopyConfig object.

        Parameters
        ----------
        cmd_string : str
            A full command string, e.g., 'robocopy C:\Src D:\Dst /S /E'.

        Returns
        -------
        RobocopyConfig
            The configured object.

        Raises
        ------
        ValueError
            If the command string does not start with 'robocopy'.
        """
        tokens = shlex.split(cmd_string)
        if not tokens or tokens[0].lower() != "robocopy":
            raise ValueError("Command string must start with 'robocopy'")

        # Basic path extraction (assumes robocopy <src> <dst> [files])
        src = Path(tokens[1])
        dst = Path(tokens[2])
        files = (
            tokens[3] if len(tokens) > 3 and not tokens[3].startswith("/") else "*.*"
        )

        config = cls(
            source=src,
            destination=dst,
            files=files,
        )

        i = 4
        while i < len(tokens):
            token = tokens[i]
            t = token.upper()

            if t in _BOOLEAN_FLAGS:
                path = _BOOLEAN_FLAGS[t]
                if len(path) == 2:
                    setattr(getattr(config, path[0]), path[1], True)
                else:
                    setattr(config, path[0], True)
            elif t == "/MIR":
                config.copy.mirror = True
                config.copy.empty_subdirs = True
                config.copy.purge = True
            elif t == "/XF":
                while i + 1 < len(tokens) and not tokens[i + 1].startswith("/"):
                    i += 1
                    config.selection.exclude_files.append(tokens[i])
            elif t == "/XD":
                while i + 1 < len(tokens) and not tokens[i + 1].startswith("/"):
                    i += 1
                    config.selection.exclude_dirs.append(tokens[i])
            else:
                for prefix, (path, type_func) in _PREFIX_FLAGS.items():
                    if t.startswith(prefix):
                        val = type_func(t.split(":", 1)[1])
                        if len(path) == 2:
                            setattr(getattr(config, path[0]), path[1], val)
                        else:
                            setattr(config, path[0], val)
                        break

            i += 1

        return config

    def to_args(self) -> list[str]:
        """Convert this configuration into a list of robocopy arguments.

        Returns
        -------
        list[str]
            A list of command-line arguments compatible with subprocess.
        """
        args = [
            "robocopy",
            str(self.source),
            str(self.destination),
            self.files,
        ]
        self._add_copy_args(args)
        self._add_selection_args(args)
        self._add_logging_args(args)

        args.append(f"/R:{self.retry_count}")
        args.append(f"/W:{self.retry_wait}")

        return args

    def _add_copy_args(self, args: list[str]) -> None:
        """Add copy configuration flags to the argument list."""
        if self.copy.subdirs:
            args.append("/S")
        if self.copy.empty_subdirs:
            args.append("/E")
        if self.copy.restartable:
            args.append("/Z")
        if self.copy.backup_mode:
            args.append("/B")
        if self.copy.mirror:
            args.append("/MIR")
        if self.copy.purge:
            args.append("/PURGE")
        args.append(f"/MT:{self.copy.multi_threaded}")
        if self.copy.fat_file_times:
            args.append("/FFT")

    def _add_selection_args(self, args: list[str]) -> None:
        """Add selection configuration flags to the argument list."""
        if self.selection.exclude_older:
            args.append("/XO")
        if self.selection.exclude_extra:
            args.append("/XX")
        if self.selection.exclude_files:
            args.extend(["/XF", *self.selection.exclude_files])
        if self.selection.exclude_dirs:
            args.extend(["/XD", *self.selection.exclude_dirs])
        if self.selection.extra_flags:
            args.extend(self.selection.extra_flags)

    def _add_logging_args(self, args: list[str]) -> None:
        """Add logging configuration flags to the argument list."""
        if self.logging.verbose:
            args.append("/V")
        if self.logging.no_file_list:
            args.append("/NFL")
        if self.logging.no_dir_list:
            args.append("/NDL")
        if self.logging.show_timestamps:
            args.append("/TS")
        if self.logging.full_pathnames:
            args.append("/FP")
        if self.logging.bytes_as_integers:
            args.append("/BYTES")
        if self.logging.tee:
            args.append("/TEE")
