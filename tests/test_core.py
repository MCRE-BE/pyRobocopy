####################
# Import Statement #
####################
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dll_etl.reusable import NothingToLoadError
from dll_etl.robocopy.core import RobocopyError, _handle_rc, robocopy


# ==================== #
# Cross-Platform Tests #
# ==================== #
def test_handle_rc_success():
    """Verify bitwise success codes."""
    assert _handle_rc(Path("."), 1, "out", "") == 1
    assert _handle_rc(Path("."), 3, "out", "") == 3
    assert _handle_rc(Path("."), 7, "out", "") == 7


def test_handle_rc_no_files():
    """Verify exit code 0 raises NothingToLoadError."""
    with pytest.raises(NothingToLoadError, match=r"No files were copied\."):
        _handle_rc(Path("."), 0, "out", "")


def test_handle_rc_errors():
    """Verify exit codes >= 8 raise RobocopyError."""
    with pytest.raises(RobocopyError, match="Some files failed to copy"):
        _handle_rc(Path("."), 8, "out", "")
    with pytest.raises(RobocopyError, match="Serious error"):
        _handle_rc(Path("."), 16, "out", "")


def test_robocopy_src_not_exists():
    """Verify robocopy fails if source is missing."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        pytest.raises(NothingToLoadError, match=r"Source directory .* does not exist"),
    ):
        robocopy("non_existent_src", "dst")


def test_robocopy_calls_subprocess():
    """Verify robocopy builds command and calls subprocess.run."""
    with patch("pathlib.Path.exists", return_value=True), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="Copied", stderr="")

        # Use specific flags to check they are included
        rc = robocopy("src", "dst", exclude_older=True, restartable=True)

        assert rc == 1
        args = mock_run.call_args[0][0]
        assert "robocopy" in args
        assert "src" in args
        assert "dst" in args
        assert "/XO" in args  # exclude_older
        assert "/Z" in args  # restartable
        assert "/MT:16" in args  # default threads


def test_robocopy_extra_flags_and_excludes():
    """Verify extra flags and file exclusions are correctly handled."""
    with patch("pathlib.Path.exists", return_value=True), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="Copied", stderr="")

        robocopy("src", "dst", exclude_files=["f1.txt", "f2.log"], extra_flags=["/XJ"])

        args = mock_run.call_args[0][0]
        assert "/XF" in args
        assert "f1.txt" in args
        assert "f2.log" in args
        assert "/XJ" in args
