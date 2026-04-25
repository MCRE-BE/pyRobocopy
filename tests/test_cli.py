import sys
from unittest.mock import patch

from robocopy.cli import main


def test_cli_help(capsys):
    import pytest

    with patch.object(sys, "argv", ["pyrobocopy", "help"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    out, _err = capsys.readouterr()
    assert "Usage: pyrobocopy [OPTIONS]" in out
    assert "--backend=windows" in out
    assert "--backend=python" in out


def test_cli_interactive(capsys):
    import pytest

    with patch.object(sys, "argv", ["pyrobocopy", "--language=interactive"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    out, _err = capsys.readouterr()
    assert "Interactive CLI interface is not yet implemented." in out


def test_cli_python_backend(capsys):
    import pytest

    with patch.object(sys, "argv", ["pyrobocopy", "--language=python", "-h"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    out, _err = capsys.readouterr()
    assert "Python argparse backend for pyrobocopy" in out


def test_cli_unknown_backend(capsys):
    import pytest

    with patch.object(sys, "argv", ["pyrobocopy", "--language=unknown", "a", "b"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    out, _err = capsys.readouterr()
    assert "Unknown backend: unknown" in out


from robocopy.cli import parse_python_backend


def test_parse_python_backend_defaults():
    args = ["/src", "/dst"]
    config, smart_progress = parse_python_backend(args)

    assert str(config.source) == "/src"
    assert str(config.destination) == "/dst"
    assert config.files == "*.*"
    assert config.copy.subdirs is False
    assert config.copy.multi_threaded == 8
    assert smart_progress is False


def test_parse_python_backend_long_args():
    args = [
        "/src",
        "/dst",
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
    args = ["/src", "/dst", "-s", "-mt", "32", "-xo", "-v"]
    config, smart_progress = parse_python_backend(args)

    assert config.copy.subdirs is True
    assert config.copy.multi_threaded == 32
    assert config.selection.exclude_older is True
    assert config.logging.verbose is True
    assert smart_progress is False


@patch("robocopy.cli.RobocopyRunner")
def test_cli_windows_backend(mock_runner):
    import pytest

    # Mock the runner to return a dummy result
    mock_instance = mock_runner.return_value
    mock_instance.run.return_value.exit_code = 0

    with patch.object(sys, "argv", ["pyrobocopy", "--backend=windows", "/src", "/dst", "*.*", "/S"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    mock_runner.assert_called_once()
    # The config should have parsed /S
    config = mock_runner.call_args[0][0]
    assert str(config.source) == "/src"
    assert str(config.destination) == "/dst"
    assert config.copy.subdirs is True


@patch("robocopy.cli.RobocopyRunner")
def test_cli_python_backend_execution(mock_runner):
    import pytest

    mock_instance = mock_runner.return_value
    mock_instance.run.return_value.exit_code = 0

    with patch.object(sys, "argv", ["pyrobocopy", "--backend=python", "/src", "/dst", "-s"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

    mock_runner.assert_called_once()
    config = mock_runner.call_args[0][0]
    assert str(config.source) == "/src"
    assert str(config.destination) == "/dst"
    assert config.copy.subdirs is True
