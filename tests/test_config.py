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


def test_from_command_line_invalid():
    import pytest
    with pytest.raises(ValueError, match="must start with"):
        RobocopyConfig.from_command_line("notrobocopy src dst")

def test_from_command_line_mir():
    config = RobocopyConfig.from_command_line("robocopy src dst /MIR")
    assert config.copy.mirror is True
    assert config.copy.empty_subdirs is True
    assert config.copy.purge is True

def test_from_command_line_prefix_flags():
    config = RobocopyConfig.from_command_line("robocopy src dst /R:10 /W:5 /MT:32")
    assert config.retry_count == 10
    assert config.retry_wait == 5
    assert config.copy.multi_threaded == 32

def test_config_validate_empty_path():
    from pathlib import Path

    import pytest

    from robocopy.config import RobocopyConfig
    config = RobocopyConfig(source=Path("."), destination=Path("dst"))
    with pytest.raises(ValueError, match="source path cannot be empty"):
        config.validate()

def test_from_command_line_boolean_flags():
    from robocopy.config import RobocopyConfig
    config = RobocopyConfig.from_command_line("robocopy src dst /V")
    assert config.logging.verbose is True

def test_from_command_line_xf_xd_bug():
    from robocopy.config import RobocopyConfig
    config = RobocopyConfig.from_command_line("robocopy src dst /XD dir1 dir2 /XF file1.txt file2.txt")
    assert "dir1" in config.selection.exclude_dirs
    assert "dir2" in config.selection.exclude_dirs
    assert "file1.txt" in config.selection.exclude_files
    assert "file2.txt" in config.selection.exclude_files

def test_from_command_line_boolean_flag_top_level_patched():
    # Since there are no top level _BOOLEAN_FLAGS, we mock one temporarily to hit that code path
    from robocopy.config import _BOOLEAN_FLAGS, RobocopyConfig
    _BOOLEAN_FLAGS["/DUMMY_BOOL"] = ("retry_count", "")
    config = RobocopyConfig.from_command_line("robocopy src dst /DUMMY_BOOL")
    assert config.retry_count is True
    # Clean up
    del _BOOLEAN_FLAGS["/DUMMY_BOOL"]
