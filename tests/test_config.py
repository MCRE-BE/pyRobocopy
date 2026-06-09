# %%
####################
# Import Statement #
####################
from pathlib import Path
from unittest.mock import patch

import pytest

from robocopy.config import (
    CopyOptions,
    LoggingOptions,
    RobocopyConfig,
    SelectionOptions,
)


@pytest.fixture(autouse=True)
def mock_shutil_which():
    """Mock shutil.which to return 'robocopy' for stable configuration test outputs."""
    with patch("shutil.which", return_value="robocopy"):
        yield


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


def test_import_compatibility_fallback():
    """Test that the import fallback for Self works on older Python versions."""
    import importlib
    from unittest.mock import MagicMock, patch

    import robocopy.config

    # We simulate a Python version < 3.11 and ensure typing_extensions is mocked
    mock_typing_extensions = MagicMock()
    mock_typing_extensions.Self = "MockSelf"

    with (
        patch.dict(
            "sys.modules",
            {"typing_extensions": mock_typing_extensions},
        ),
        patch(
            "sys.version_info",
            (3, 10, 0),
        ),
    ):
        # Force a reload of the module to re-execute the import logic
        importlib.reload(robocopy.config)
        # Verify it used typing_extensions.Self
        assert robocopy.config.Self == "MockSelf"

    # Restore the module state for subsequent tests
    importlib.reload(robocopy.config)


def test_find_robocopy_executable_custom_path():
    """Verify that a valid absolute path returned by shutil.which that is not a wrapper is returned."""
    from unittest.mock import patch

    from robocopy.config import _find_robocopy_executable

    with patch("shutil.which", return_value="/usr/local/bin/robocopy"), patch("sys.prefix", "/venv"):
        res = _find_robocopy_executable()
        assert res == "/usr/local/bin/robocopy"


def test_find_robocopy_executable_windows_system32():
    """Verify that on Windows, if shutil.which returns a Python wrapper, it finds System32/robocopy.exe."""
    from unittest.mock import patch

    from robocopy.config import _find_robocopy_executable

    # Mock shutil.which to return a wrapper path in sys.prefix
    wrapper_path = "C:\\my_project\\.venv\\Scripts\\robocopy.exe"
    with (
        patch("shutil.which", return_value=wrapper_path),
        patch("sys.prefix", "C:\\my_project\\.venv"),
        patch("sys.exec_prefix", "C:\\my_project\\.venv"),
        patch("sys.platform", "win32"),
        patch("os.path.exists", return_value=True),
    ):
        res = _find_robocopy_executable()
        # Should return System32 candidate first
        assert "System32\\robocopy.exe" in res or "System32/robocopy.exe" in res


def test_find_robocopy_executable_fallback_path():
    """Verify that it scans PATH excluding python wrapper folders."""
    import os
    from unittest.mock import patch

    from robocopy.config import _find_robocopy_executable

    # Mock shutil.which to return a wrapper path in sys.prefix,
    # and mock exists for System32 to be False (to trigger fallback)
    wrapper_path = "/venv/bin/robocopy"

    def mock_exists_side_effect(path):
        # Fail the Windows system checks
        return not ("System32" in str(path) or "SysWOW64" in str(path))

    def mock_isfile_side_effect(path):
        normalized = str(path).replace("\\", "/").lower()
        return "other/bin/robocopy" in normalized

    with (
        patch("shutil.which", return_value=wrapper_path),
        patch("sys.prefix", "/venv"),
        patch("sys.exec_prefix", "/venv"),
        patch("sys.platform", "linux"),
        patch("os.path.exists", side_effect=mock_exists_side_effect),
        patch("os.path.isfile", side_effect=mock_isfile_side_effect),
        patch("os.access", return_value=True),
        patch.dict("os.environ", {"PATH": f"/venv/bin{os.pathsep}/other/bin"}),
    ):
        res = _find_robocopy_executable()
        # Should skip /venv/bin/robocopy and find /other/bin/robocopy
        assert res.replace("\\", "/").lower().endswith("other/bin/robocopy")


def test_find_robocopy_executable_last_resort():
    """Verify that if all else fails, it returns 'robocopy'."""
    from unittest.mock import patch

    from robocopy.config import _find_robocopy_executable

    with (
        patch("shutil.which", return_value=None),
        patch("sys.platform", "linux"),
        patch.dict("os.environ", {"PATH": ""}),
    ):
        res = _find_robocopy_executable()
        assert res == "robocopy"
