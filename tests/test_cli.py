import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from robocopy.cli import (
    _get_config_and_smart_progress,
    _get_python_backend_parser,
    main,
    parse_python_backend,
    print_help,
)


def test_print_help(capsys):
    """Verify that print_help outputs the expected help text."""
    print_help()
    out, _ = capsys.readouterr()
    assert "Usage: pyrobocopy [OPTIONS]" in out
    assert "--backend=windows" in out
    assert "--backend=python" in out
    assert "interactive" in out.lower()


def test_cli_interactive():
    """Verify that the interactive backend launches the TUI."""
    # Test via --backend
    with patch("robocopy.interactive.RobocopyInteractive.run") as mock_run:
        with patch.object(sys, "argv", ["pyrobocopy", "src", "dst", "--backend=interactive"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 0
        mock_run.assert_called_once()


def test_cli_python_backend(capsys):
    with patch.object(sys, "argv", ["pyrobocopy", "--language=python", "-h"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    out, _err = capsys.readouterr()
    assert "Python argparse backend for pyrobocopy" in out


def test_cli_unknown_backend(capsys):
    with patch.object(sys, "argv", ["pyrobocopy", "--language=unknown", "a", "b"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    out, _err = capsys.readouterr()
    assert "Unknown backend: unknown" in out


def test_parse_python_backend_defaults():
    args = ["src", "dst"]
    config, smart_progress = parse_python_backend(args)

    assert str(config.source) == "src"
    assert str(config.destination) == "dst"
    assert config.files == "*.*"
    assert config.copy.subdirs is False
    assert config.copy.multi_threaded == 8
    assert smart_progress is False


def test_parse_python_backend_long_args():
    args = [
        "src",
        "dst",
        "*.py",
        "*.txt",
        "--subdirs",
        "--multi-threaded",
        "16",
        "--exclude-older",
        "--smart-progress",
    ]
    config, smart_progress = parse_python_backend(args)

    assert config.files == "*.py *.txt"
    assert config.copy.subdirs is True
    assert config.copy.multi_threaded == 16
    assert config.selection.exclude_older is True
    assert smart_progress is True


def test_parse_python_backend_short_args():
    args = ["src", "dst", "-s", "-mt", "32", "-xo", "-v"]
    config, smart_progress = parse_python_backend(args)

    assert config.copy.subdirs is True
    assert config.copy.multi_threaded == 32
    assert config.selection.exclude_older is True
    assert config.logging.verbose is True
    assert smart_progress is False


@patch("robocopy.cli.RobocopyRunner")
def test_cli_windows_backend(mock_runner):
    # Mock the runner to return a dummy result
    mock_instance = mock_runner.return_value
    mock_instance.run.return_value.exit_code = 0

    with patch.object(sys, "argv", ["pyrobocopy", "--backend=windows", "src", "dst", "*.*", "/S"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    mock_runner.assert_called_once()
    # The config should have parsed /S
    config = mock_runner.call_args[0][0]
    assert str(config.source) == "src"
    assert str(config.destination) == "dst"
    assert config.copy.subdirs is True


@patch("robocopy.cli.RobocopyRunner")
def test_cli_python_backend_execution(mock_runner):
    mock_instance = mock_runner.return_value
    mock_instance.run.return_value.exit_code = 0

    with patch.object(sys, "argv", ["pyrobocopy", "--backend=python", "src", "dst", "-s"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    mock_runner.assert_called_once()
    config = mock_runner.call_args[0][0]
    assert str(config.source) == "src"
    assert str(config.destination) == "dst"
    assert config.copy.subdirs is True


def test_main_cli_help_no_args(capsys):
    with patch.object(sys, "argv", ["pyrobocopy"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
    out, _ = capsys.readouterr()
    assert "Usage: pyrobocopy" in out


def test_main_nothing_to_load_error(capsys):
    from robocopy.error import NothingToLoadError

    with patch("robocopy.cli.RobocopyRunner") as mock_runner:
        mock_instance = mock_runner.return_value
        mock_instance.run.side_effect = NothingToLoadError("Fake error")
        with patch.object(sys, "argv", ["pyrobocopy", "src", "dst", "--backend=windows"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1
        out, _ = capsys.readouterr()
        assert "Fake error" in out


def test_main_windows_backend_quoted_spaces(capsys):
    with patch("robocopy.cli.RobocopyRunner") as mock_runner:
        mock_instance = mock_runner.return_value
        mock_instance.run.return_value.exit_code = 0
        with patch.object(sys, "argv", ["pyrobocopy", "src path", "dst", "--backend=windows"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 0
        config = mock_runner.call_args[0][0]
        assert str(config.source) == "src path"


def test_main_cli_backend_empty_remaining(capsys):
    with patch.object(sys, "argv", ["pyrobocopy", "--backend=windows"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
    out, _ = capsys.readouterr()
    assert "Usage: pyrobocopy" in out


def test_get_python_backend_parser():
    parser = _get_python_backend_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "pyrobocopy --backend=python"
    assert parser.description == "Python argparse backend for pyrobocopy"

    # Test defaults
    args = ["src", "dst"]
    parsed = parser.parse_args(args)
    assert parsed.source == Path("src")
    assert parsed.destination == Path("dst")
    assert parsed.files == ["*.*"]
    assert parsed.multi_threaded == 8
    assert parsed.exclude_older is True
    assert parsed.no_dir_list is True
    assert parsed.retry_count == 3

    # Test overridden values
    args = ["src", "dst", "f1", "-s", "-mt", "16", "--no-exclude-older", "--list-dirs"]
    parsed = parser.parse_args(args)
    assert parsed.files == ["f1"]
    assert parsed.subdirs is True
    assert parsed.multi_threaded == 16
    assert parsed.exclude_older is False
    assert parsed.no_dir_list is False


def test_get_config_and_smart_progress():
    # Test python backend
    config, smart_progress = _get_config_and_smart_progress("python", ["src", "dst", "--smart-progress"])
    assert str(config.source) == "src"
    assert smart_progress is True

    # Test windows backend
    config, smart_progress = _get_config_and_smart_progress("windows", ["src", "dst", "/S"])
    assert str(config.source) == "src"
    assert config.copy.subdirs is True
    assert smart_progress is False

    # Test unknown backend
    with pytest.raises(SystemExit) as e:
        _get_config_and_smart_progress("unknown", ["src", "dst"])
    assert e.value.code == 1
