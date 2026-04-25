import argparse
import sys
from pathlib import Path

from .config import CopyOptions, LoggingOptions, RobocopyConfig, SelectionOptions
from .error import NothingToLoadError
from .runner import RobocopyRunner


def print_help() -> None:
    print("Usage: pyrobocopy [OPTIONS] source destination [files] [robocopy_flags]")  # noqa: T201
    print()  # noqa: T201
    print("Alternative backends:")  # noqa: T201
    print("  --backend=windows    (Default) Passes arguments natively to the Robocopy parser.")  # noqa: T201
    print("  --backend=python     Uses Python-style argparse flags (e.g. --source, --copy-subdirs).")  # noqa: T201
    print("  --backend=interactive Interactive CLI interface (Not yet implemented).")  # noqa: T201
    print()  # noqa: T201
    print("Commands:")  # noqa: T201
    print("  help                 Show this help message.")  # noqa: T201
    print()  # noqa: T201


def parse_python_backend(args: list[str]) -> tuple[RobocopyConfig, bool]:
    parser = argparse.ArgumentParser(
        prog="pyrobocopy --backend=python",
        description="Python argparse backend for pyrobocopy",
    )

    # Required arguments (positional)
    parser.add_argument("source", type=Path, help="Source directory")
    parser.add_argument("destination", type=Path, help="Destination directory")

    # Optional positional
    parser.add_argument("files", nargs="*", default=["*.*"], help="File filter (default: *.*)")

    # Copy options
    copy_group = parser.add_argument_group("Copy Options")
    copy_group.add_argument("--subdirs", action="store_true", help="Copy subdirectories")
    copy_group.add_argument("--empty-subdirs", action="store_true", help="Copy empty subdirectories")
    copy_group.add_argument("--restartable", action="store_true", help="Restartable mode")
    copy_group.add_argument("--backup-mode", action="store_true", help="Backup mode")
    copy_group.add_argument("--multi-threaded", type=int, default=8, help="Multithreading count")
    copy_group.add_argument("--fat-file-times", action="store_true", default=True, help="FAT file times")
    copy_group.add_argument("--no-fat-file-times", action="store_false", dest="fat_file_times")
    copy_group.add_argument("--copy-flags", type=str, default="DAT", help="Copy flags (default: DAT)")
    copy_group.add_argument("--dir-copy-flags", type=str, default="DA", help="Dir copy flags (default: DA)")
    copy_group.add_argument("--purge", action="store_true", help="Purge destination files")
    copy_group.add_argument("--mirror", action="store_true", help="Mirror mode")

    # Selection options
    sel_group = parser.add_argument_group("Selection Options")
    sel_group.add_argument("--exclude-older", action="store_true", default=True, help="Exclude older files")
    sel_group.add_argument("--no-exclude-older", action="store_false", dest="exclude_older")
    sel_group.add_argument("--exclude-extra", action="store_true", help="Exclude extra files")
    sel_group.add_argument("--exclude-files", nargs="*", default=[], help="Exclude files")
    sel_group.add_argument("--exclude-dirs", nargs="*", default=[], help="Exclude dirs")
    sel_group.add_argument("--include-archive-only", action="store_true", help="Include archive only")
    sel_group.add_argument("--reset-archive", action="store_true", help="Reset archive attribute")

    # Logging options
    log_group = parser.add_argument_group("Logging Options")
    log_group.add_argument("--verbose", action="store_true", help="Verbose logging")
    log_group.add_argument("--no-file-list", action="store_true", help="No file list")
    log_group.add_argument("--no-dir-list", action="store_true", default=True, help="No dir list")
    log_group.add_argument("--list-dirs", action="store_false", dest="no_dir_list")
    log_group.add_argument("--show-timestamps", action="store_true", help="Show timestamps")
    log_group.add_argument("--full-pathnames", action="store_true", help="Full pathnames")
    log_group.add_argument("--bytes-as-integers", action="store_true", default=True, help="Bytes as integers")
    log_group.add_argument("--no-job-header", action="store_true", help="No job header")
    log_group.add_argument("--no-job-summary", action="store_true", help="No job summary")
    log_group.add_argument("--tee", action="store_true", help="Tee output")

    # Retries
    parser.add_argument("--retry-count", type=int, default=3, help="Retry count")
    parser.add_argument("--retry-wait", type=int, default=3, help="Retry wait")

    # Runner args
    parser.add_argument("--smart-progress", action="store_true", help="Use smart progress")

    parsed_args = parser.parse_args(args)

    copy_opts = CopyOptions(
        subdirs=parsed_args.subdirs,
        empty_subdirs=parsed_args.empty_subdirs,
        restartable=parsed_args.restartable,
        backup_mode=parsed_args.backup_mode,
        multi_threaded=parsed_args.multi_threaded,
        fat_file_times=parsed_args.fat_file_times,
        copy_flags=parsed_args.copy_flags,
        dir_copy_flags=parsed_args.dir_copy_flags,
        purge=parsed_args.purge,
        mirror=parsed_args.mirror,
    )

    sel_opts = SelectionOptions(
        exclude_older=parsed_args.exclude_older,
        exclude_extra=parsed_args.exclude_extra,
        exclude_files=parsed_args.exclude_files,
        exclude_dirs=parsed_args.exclude_dirs,
        include_archive_only=parsed_args.include_archive_only,
        reset_archive=parsed_args.reset_archive,
    )

    log_opts = LoggingOptions(
        verbose=parsed_args.verbose,
        no_file_list=parsed_args.no_file_list,
        no_dir_list=parsed_args.no_dir_list,
        show_timestamps=parsed_args.show_timestamps,
        full_pathnames=parsed_args.full_pathnames,
        bytes_as_integers=parsed_args.bytes_as_integers,
        no_job_header=parsed_args.no_job_header,
        no_job_summary=parsed_args.no_job_summary,
        tee=parsed_args.tee,
    )

    config = RobocopyConfig(
        source=parsed_args.source,
        destination=parsed_args.destination,
        files=" ".join(parsed_args.files),
        copy=copy_opts,
        selection=sel_opts,
        logging=log_opts,
        retry_count=parsed_args.retry_count,
        retry_wait=parsed_args.retry_wait,
    )

    return config, parsed_args.smart_progress


def main() -> None:  # noqa: C901, PLR0912
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print_help()
        sys.exit(0)

    backend = "windows"
    remaining_args = []

    for arg in args:
        if arg.startswith("--backend="):
            backend = arg.split("=", 1)[1]
        elif arg == "--language=python":
            backend = "python"
        elif arg.startswith("--language="):
            backend = arg.split("=", 1)[1]
        else:
            remaining_args.append(arg)

    if not remaining_args and backend != "interactive":
        print_help()
        sys.exit(1)

    if backend == "interactive":
        print("Interactive CLI interface is not yet implemented.")  # noqa: T201
        sys.exit(0)
    elif backend == "python":
        config, smart_progress = parse_python_backend(remaining_args)
    elif backend == "windows":
        # Quote arguments that contain spaces but keep the robocopy prefix
        cmd_parts = ["robocopy"]
        for arg in remaining_args:
            if " " in arg and not arg.startswith('"') and not arg.endswith('"'):
                cmd_parts.append(f'"{arg}"')
            else:
                cmd_parts.append(arg)
        cmd_string = " ".join(cmd_parts)
        config = RobocopyConfig.from_command_line(cmd_string)
        smart_progress = False
    else:
        print(f"Unknown backend: {backend}")  # noqa: T201
        sys.exit(1)

    runner = RobocopyRunner(config)
    try:
        result = runner.run(smart_progress=smart_progress)
        sys.exit(result.exit_code)
    except NothingToLoadError as e:
        print(f"Error: {e}")  # noqa: T201
        sys.exit(1)
