"""Tests for the modernized robocopy library."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from robocopy import (
    NothingToLoadError,
    RobocopyConfig,
    RobocopyRunner,
    robocopy,
)


# ==================== #
# Functional API Tests #
# ==================== #
def test_robocopy_src_not_exists():
    """Verify robocopy fails if source is missing."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        pytest.raises(NothingToLoadError, match=r"Source .* does not exist"),
    ):
        robocopy("non_existent_src", "dst")


def test_robocopy_calls_runner():
    """Verify the functional wrapper correctly initializes the runner."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "robocopy.RobocopyRunner.run",
        ) as mock_run,
    ):
        mock_run.return_value = MagicMock(
            exit_code=1,
            stats=MagicMock(
                files=MagicMock(total=5),
            ),
        )
        status = robocopy("src", "dst", threads=8)

        assert status == 1
        mock_run.assert_called_once()


def test_robocopy_no_files_found():
    """Verify that if exit code is 0 but 0 files were found, NothingToLoadError is raised."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("robocopy.RobocopyRunner.run") as mock_run,
    ):
        # Mocking result: exit_code 0, but total files 0
        mock_result = MagicMock()
        mock_result.exit_code = 0
        mock_result.stats.files.total = 0
        mock_run.return_value = mock_result

        with pytest.raises(NothingToLoadError, match="No files found to copy"):
            robocopy("src", "dst")


# ==================== #
# Runner Class Tests   #
# ==================== #
def test_runner_run_source_not_exists():
    """Verify that runner.run() raises NothingToLoadError if source does not exist."""
    config = RobocopyConfig(source=Path("non_existent_src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with (
        patch("pathlib.Path.exists", return_value=False),
        pytest.raises(NothingToLoadError, match=r"Source .* does not exist."),
    ):
        runner.run()


def test_runner_logger_injection():
    """Verify that a custom logger can be passed to the runner."""
    custom_logger = logging.getLogger("custom_test_logger")
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))

    runner = RobocopyRunner(config=config, logger=custom_logger)

    assert runner.log == custom_logger


def test_runner_default_logger():
    """Verify defaults to 'robocopy' logger if none provided."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    assert runner.log.name == "robocopy"


def test_runner_run_execution():
    """Test the core run execution calling subprocess.Popen."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("subprocess.Popen") as mock_popen,
    ):
        # Setting up mock for Popen
        process_mock = MagicMock()
        process_mock.stdout = []
        process_mock.returncode = 1
        process_mock.__enter__.return_value = process_mock
        mock_popen.return_value = process_mock

        result = runner.run()

        assert result.exit_code == 1
        assert mock_popen.called


def test_runner_discover_totals_valid():
    """Verify that discover_totals returns the expected file count."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Files : 100 200 300\n"
        mock_run.return_value = mock_proc

        assert runner.discover_totals() == 100


def test_runner_discover_totals_malformed_index_error():
    """Verify that discover_totals handles malformed output correctly (IndexError)."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Files :\n"  # Too few elements, parts will be ['Files', ':']
        mock_run.return_value = mock_proc

        assert runner.discover_totals() == 0


def test_runner_discover_totals_malformed_value_error():
    """Verify that discover_totals handles malformed output correctly (ValueError)."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Files : text anothertext\n"  # Invalid integer
        mock_run.return_value = mock_proc

        assert runner.discover_totals() == 0


def test_runner_discover_totals_no_files_line():
    """Verify that discover_totals returns 0 if the target line is not found."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Other output\n"
        mock_run.return_value = mock_proc

        assert runner.discover_totals() == 0


def test_runner_run_exception_handling():
    """Verify that exceptions during subprocess execution are caught and handled."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("subprocess.Popen", side_effect=OSError("Permission denied")),
        patch.object(runner.log, "error") as mock_log_error,
    ):
        result = runner.run()

        assert result.exit_code == 16
        assert "Permission denied" in result.errors
        mock_log_error.assert_any_call("Robocopy run failed fatally.", exc_info=True)
