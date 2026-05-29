"""Tests for the interactive TUI backend."""

from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import Button, Input, Switch

from robocopy.interactive import RobocopyInteractive


@pytest.mark.asyncio
async def test_interactive_app_mount():
    """Test that the app mounts and initializes the command string."""
    app = RobocopyInteractive()
    async with app.run_test() as pilot:
        # Check initial state
        assert "robocopy" in app.command_str
        assert "C:\\Source" in app.command_str
        assert "D:\\Destination" in app.command_str
        await pilot.exit(None)


@pytest.mark.asyncio
async def test_interactive_clear_buttons():
    """Test the clear buttons for source and destination."""
    app = RobocopyInteractive()
    async with app.run_test() as pilot:
        # Clear source
        btn_source = app.query_one("#btn-clear-source", Button)
        btn_source.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.query_one("#input-source", Input).value == ""

        # Clear destination
        btn_dest = app.query_one("#btn-clear-dest", Button)
        btn_dest.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.query_one("#input-destination", Input).value == ""

        # Clear files
        btn_files = app.query_one("#btn-clear-files", Button)
        btn_files.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.query_one("#input-files", Input).value == ""
        await pilot.exit(None)


@pytest.mark.asyncio
async def test_interactive_command_generation():
    """Test that the generate button correctly builds the command string."""
    app = RobocopyInteractive()
    async with app.run_test() as pilot:
        # Change input values
        app.query_one("#input-source", Input).value = "C:\\NewSource"
        app.query_one("#input-destination", Input).value = "D:\\NewDest"
        app.query_one("#input-files", Input).value = "*.txt"

        # Toggle a switch (Subdirs)
        switch = app.query_one("#flag-S", Switch)
        switch.value = True

        # Click generate
        btn_gen = app.query_one("#btn-generate-cmd", Button)
        btn_gen.focus()
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.command_str
        assert "C:\\NewSource" in cmd
        assert "D:\\NewDest" in cmd
        assert "*.txt" in cmd
        assert "/S" in cmd

        # Test empty file filter (hits the else block)
        app.query_one("#input-files", Input).value = ""
        btn_gen.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert "*.*" in app.command_str

        await pilot.exit(None)


@pytest.mark.asyncio
async def test_interactive_execute_sync():
    """Test that the execute sync button triggers the runner."""
    app = RobocopyInteractive()

    mock_result = MagicMock()
    mock_result.exit_code = 0

    with patch("robocopy.interactive.RobocopyRunner") as mock_runner_cls:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = mock_result

        async with app.run_test() as pilot:
            # Click execute
            btn_run = app.query_one("#btn-run", Button)
            btn_run.focus()
            await pilot.press("enter")

            # Since it runs in a thread, we might need a small wait
            # for the worker to start and finish.
            # In run_test, we can wait for workers.
            await pilot.wait_for_scheduled_animations()

            # Verify runner was initialized and run called
            mock_runner_cls.assert_called_once()
            mock_runner.run.assert_called_once()

            await pilot.exit(None)


@pytest.mark.asyncio
async def test_interactive_execute_sync_failure():
    """Test that the execute sync handles runner failures gracefully."""
    app = RobocopyInteractive()

    with patch("robocopy.interactive.RobocopyRunner") as mock_runner_cls:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.side_effect = Exception("Mock failure")

        async with app.run_test() as pilot:
            # Click execute
            btn_run = app.query_one("#btn-run", Button)
            btn_run.focus()
            await pilot.press("enter")

            await pilot.wait_for_scheduled_animations()

            # Verify runner was initialized and run called
            mock_runner_cls.assert_called_once()
            mock_runner.run.assert_called_once()

            await pilot.exit(None)


@pytest.mark.asyncio
async def test_interactive_quit():
    """Test that the quit action exits the app."""
    app = RobocopyInteractive()
    async with app.run_test() as pilot:
        await app.action_quit()
        await pilot.exit(None)


@pytest.mark.asyncio
async def test_interactive_all_options():
    """Test that all new options (inputs, switches) are correctly read and built into the config."""
    app = RobocopyInteractive()
    async with app.run_test() as pilot:
        # Check defaults
        config, smart_progress = app._build_config_from_ui()
        assert config.copy.multi_threaded == 8
        assert config.copy.copy_flags == "DAT"
        assert config.copy.dir_copy_flags == "DA"
        assert config.selection.exclude_older is True
        assert config.logging.no_dir_list is True
        assert config.logging.bytes_as_integers is True
        assert config.retry_count == 3
        assert config.retry_wait == 3
        assert smart_progress is False

        # Set custom values
        app.query_one("#input-flag-MT", Input).value = "16"
        app.query_one("#input-flag-COPY", Input).value = "D"
        app.query_one("#input-flag-DCOPY", Input).value = "T"
        app.query_one("#input-flag-XF", Input).value = "*.tmp *.log"
        app.query_one("#input-flag-XD", Input).value = "temp cache"
        app.query_one("#flag-XO", Switch).value = False
        app.query_one("#flag-NJH", Switch).value = True
        app.query_one("#flag-NJS", Switch).value = True
        app.query_one("#input-flag-R", Input).value = "5"
        app.query_one("#input-flag-W", Input).value = "10"
        app.query_one("#flag-smart-progress", Switch).value = True

        # Click generate to verify preview formats correctly
        btn_gen = app.query_one("#btn-generate-cmd", Button)
        btn_gen.focus()
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.command_str
        assert "/MT:16" in cmd
        assert "/COPY:D" in cmd
        assert "/DCOPY:T" in cmd
        assert "/XF" in cmd
        assert "*.tmp" in cmd
        assert "*.log" in cmd
        assert "/XD" in cmd
        assert "temp" in cmd
        assert "cache" in cmd
        assert "/XO" not in cmd
        assert "/NJH" in cmd
        assert "/NJS" in cmd
        assert "/R:5" in cmd
        assert "/W:10" in cmd

        # Check built config again
        config, smart_progress = app._build_config_from_ui()
        assert config.copy.multi_threaded == 16
        assert config.copy.copy_flags == "D"
        assert config.copy.dir_copy_flags == "T"
        assert config.selection.exclude_files == ["*.tmp", "*.log"]
        assert config.selection.exclude_dirs == ["temp", "cache"]
        assert config.selection.exclude_older is False
        assert config.logging.no_job_header is True
        assert config.logging.no_job_summary is True
        assert config.retry_count == 5
        assert config.retry_wait == 10
        assert smart_progress is True

        await pilot.exit(None)
