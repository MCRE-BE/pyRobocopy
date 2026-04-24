# %%
####################
# Import Statement #
####################
from pathlib import Path

from robocopy.config import (
    CopyOptions,
    LoggingOptions,
    RobocopyConfig,
    SelectionOptions,
)


#########
# TESTS #
#########
def test_to_args_defaults():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    args = config.to_args()
    expected = [
        "robocopy",
        "src",
        "dst",
        "*.*",
        "/MT:8",
        "/FFT",
        "/XO",
        "/NDL",
        "/BYTES",
        "/R:3",
        "/W:3",
    ]
    assert args == expected


def test_to_args_copy_options():
    config = RobocopyConfig(
        source=Path("src"),
        destination=Path("dst"),
        copy=CopyOptions(
            subdirs=True,
            empty_subdirs=True,
            restartable=True,
            backup_mode=True,
            multi_threaded=4,
            fat_file_times=False,
            purge=True,
            mirror=True,
        ),
    )
    args = config.to_args()
    assert "/S" in args
    assert "/E" in args
    assert "/Z" in args
    assert "/B" in args
    assert "/MT:4" in args
    assert "/FFT" not in args
    assert "/PURGE" in args
    assert "/MIR" in args


def test_to_args_selection_options():
    config = RobocopyConfig(
        source=Path("src"),
        destination=Path("dst"),
        selection=SelectionOptions(
            exclude_older=False,
            exclude_extra=True,
            exclude_files=["*.tmp", "*.bak"],
            exclude_dirs=["temp", "cache"],
            extra_flags=["/MIN:1024"],
        ),
    )
    args = config.to_args()
    assert "/XO" not in args
    assert "/XX" in args
    assert "/XF" in args
    assert "*.tmp" in args
    assert "*.bak" in args
    assert "/XD" in args
    assert "temp" in args
    assert "cache" in args
    assert "/MIN:1024" in args


def test_to_args_logging_options():
    config = RobocopyConfig(
        source=Path("src"),
        destination=Path("dst"),
        logging=LoggingOptions(
            verbose=True,
            no_file_list=True,
            no_dir_list=False,
            show_timestamps=True,
            full_pathnames=True,
            bytes_as_integers=False,
            tee=True,
        ),
    )
    args = config.to_args()
    assert "/V" in args
    assert "/NFL" in args
    assert "/NDL" not in args
    assert "/TS" in args
    assert "/FP" in args
    assert "/BYTES" not in args
    assert "/TEE" in args


def test_to_args_retry_options():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"), retry_count=10, retry_wait=5)
    args = config.to_args()
    assert "/R:10" in args
    assert "/W:5" in args


def test_from_command_line():
    cmd = "robocopy C:/Src D:/Dst /S /E /MT:4 /XF *.bak temp.tmp /XD dir1 dir2"
    config = RobocopyConfig.from_command_line(cmd)

    assert config.source == Path("C:/Src")
    assert config.destination == Path("D:/Dst")
    assert config.copy.subdirs is True
    assert config.copy.empty_subdirs is True
    assert config.copy.multi_threaded == 4
    assert config.selection.exclude_files == ["*.bak", "temp.tmp"]
    assert config.selection.exclude_dirs == ["dir1", "dir2"]


def test_from_command_line_mir():
    cmd = "robocopy src dst /MIR"
    config = RobocopyConfig.from_command_line(cmd)
    assert config.copy.mirror is True
    assert config.copy.empty_subdirs is True
    assert config.copy.purge is True


def test_from_command_line_exclusions():
    cmd = "robocopy src dst /XF file1.txt *.tmp /XD dir1 dir2 /S"
    config = RobocopyConfig.from_command_line(cmd)
    assert "file1.txt" in config.selection.exclude_files
    assert "*.tmp" in config.selection.exclude_files
    assert "dir1" in config.selection.exclude_dirs
    assert "dir2" in config.selection.exclude_dirs
    assert config.copy.subdirs is True


def test_from_command_line_errors():
    import pytest

    with pytest.raises(ValueError, match="Command string must start with 'robocopy'"):
        RobocopyConfig.from_command_line("notrobocopy src dst")

    with pytest.raises(ValueError, match="Command string must include source and destination paths"):
        RobocopyConfig.from_command_line("robocopy src")
