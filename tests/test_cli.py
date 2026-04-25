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
