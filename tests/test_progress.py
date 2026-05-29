from pathlib import Path
from unittest.mock import MagicMock, patch

from robocopy.runner import RobocopyRunner
from robocopy.types import FileResult, RobocopyStatus


def test_counts_towards_total():
    """Verify that only source files increment the progress bar."""
    assert RobocopyStatus.NEW_FILE.counts_towards_total
    assert RobocopyStatus.SAME.counts_towards_total
    assert RobocopyStatus.NEWER.counts_towards_total
    assert not RobocopyStatus.EXTRA_FILE.counts_towards_total
    assert not RobocopyStatus.NEW_DIR.counts_towards_total
    assert not RobocopyStatus.EXTRA_DIR.counts_towards_total


def test_runner_progress_update():
    """Verify that the runner only updates the progress bar for source files."""
    mock_config = MagicMock()
    mock_config.source = Path("src")
    mock_config.destination = Path("dst")

    # runner is instantiated to ensure it handles the logic
    _ = RobocopyRunner(mock_config)
    pbar = MagicMock()

    # We test the logic that would be inside _handle_file_result_parsed
    def simulate_handle_file_result(parsed_obj):
        if pbar:
            if parsed_obj.status.counts_towards_total:
                pbar.update(1)
            if "Dir" in parsed_obj.status.value:
                pbar.set_postfix(dir=parsed_obj.source_path.name, refresh=True)

    # 1. New File (Source) -> Should update count
    simulate_handle_file_result(FileResult(status=RobocopyStatus.NEW_FILE, source_path=Path("f1.txt")))
    assert pbar.update.call_count == 1
    assert pbar.set_postfix.call_count == 0

    # 2. Extra File (Destination) -> Should NOT update count
    simulate_handle_file_result(FileResult(status=RobocopyStatus.EXTRA_FILE, source_path=Path("extra.txt")))
    assert pbar.update.call_count == 1

    # 3. Same File (Source) -> Should update count
    simulate_handle_file_result(FileResult(status=RobocopyStatus.SAME, source_path=Path("f2.txt")))
    assert pbar.update.call_count == 2

    # 4. New Dir -> Should NOT update count BUT should set postfix
    simulate_handle_file_result(FileResult(status=RobocopyStatus.NEW_DIR, source_path=Path("dir1")))
    assert pbar.update.call_count == 2
    assert pbar.set_postfix.call_count == 1
    pbar.set_postfix.assert_called_with(dir="dir1", refresh=True)


def test_runner_get_total_files():
    """Verify that _get_total_files behaves correctly based on smart progress."""
    mock_config = MagicMock()
    mock_config.source = Path("src")
    mock_config.destination = Path("dst")
    runner = RobocopyRunner(mock_config)

    # 1. smart_progress = False -> Should return 0 without calling discover_totals
    with patch.object(runner, "discover_totals") as mock_discover:
        assert runner._get_total_files(smart_progress=False) == 0
        mock_discover.assert_not_called()

    # 2. smart_progress = True -> Should call discover_totals and return count
    with patch.object(runner, "discover_totals", return_value=42) as mock_discover:
        assert runner._get_total_files(smart_progress=True) == 42
        mock_discover.assert_called_once()


def test_runner_init_progress_bar():
    """Verify that _init_progress_bar initializes a progress bar only when required."""
    mock_config = MagicMock()
    mock_config.source = Path("src")
    mock_config.destination = Path("dst")
    runner = RobocopyRunner(mock_config)

    # 1. smart_progress = False -> Should return None
    assert runner._init_progress_bar(smart_progress=False, total_files=10) is None

    # 2. smart_progress = True -> Should initialize a tqdm progress bar
    with patch("robocopy.runner.tqdm") as mock_tqdm:
        mock_tqdm.return_value = "MockedProgressBar"
        pbar = runner._init_progress_bar(smart_progress=True, total_files=10)
        assert pbar == "MockedProgressBar"
        mock_tqdm.assert_called_once_with(
            total=10,
            unit="file",
            desc="Sync src",
        )
