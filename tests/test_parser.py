from pathlib import Path

import pytest

from robocopy.config import RobocopyConfig
from robocopy.parser import RobocopyParser


@pytest.fixture
def parser():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    return RobocopyParser(config=config)


def test_parse_line_empty(parser):
    """Test that empty lines or whitespace-only lines are ignored."""
    assert parser.parse_line("") is None
    assert parser.parse_line("   ") is None
    assert parser.parse_line("\n") is None
    assert parser.parse_line("\t") is None


def test_parse_line_error_known(parser):
    """Test matching a known error code."""
    line = "2023/10/25 10:00:00 ERROR 5 (0x00000005) Accessing Destination Directory"
    result = parser.parse_line(line)
    assert result == f"Error 5 (Access Denied): {line}"


def test_parse_line_error_unknown(parser):
    """Test matching an unknown error code."""
    line = "2023/10/25 10:00:00 ERROR 999 (0x000003E7) Something Bad Happened"
    result = parser.parse_line(line)
    assert result == f"Error 999 (Unknown Error): {line}"


def test_parse_line_summary_start(parser):
    """Test detecting the summary start line."""
    line = "               Total    Copied   Skipped  Mismatch    FAILED    Extras"
    assert not parser.stats_found
    result = parser.parse_line(line)
    assert result == "SUMMARY_START"
    assert parser.stats_found


def test_parse_line_normal_text(parser):
    """Test processing a normal line of text without error or summary."""
    line = "    New File                 100        test.txt"
    result = parser.parse_line(line)
    assert result == "New File                 100        test.txt"
