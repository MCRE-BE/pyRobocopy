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
