from unittest.mock import MagicMock

import pytest

from robocopy.config import RobocopyConfig
from robocopy.parser import RobocopyParser
from robocopy.types import FileResult, RobocopyStatus


@pytest.fixture
def parser():
    """Fixture to provide a RobocopyParser instance with a mock config."""
    mock_config = MagicMock(spec=RobocopyConfig)
    return RobocopyParser(config=mock_config)


def test_parse_line_empty(parser):
    """Test that empty or whitespace-only lines return None."""
    assert parser.parse_line("") is None
    assert parser.parse_line("   ") is None
    assert parser.parse_line("\t\n") is None


def test_parse_line_file_result(parser):
    """Test that a file status line returns a FileResult object."""
    line = "  New File  \t\t 12345  file.txt  "
    result = parser.parse_line(line)
    assert isinstance(result, FileResult)
    assert result.status == RobocopyStatus.NEW_FILE
    assert str(result.source_path).endswith("file.txt")


def test_parse_line_misc(parser):
    """Test that a non-significant line returns the stripped line."""
    line = "  This is just some text  "
    assert parser.parse_line(line) == "This is just some text"


def test_parse_line_summary_start(parser):
    """Test that the summary header sets stats_found and returns SUMMARY_START."""
    assert not parser.stats_found
    line = "               Total    Copied   Skipped  Mismatch    FAILED    Extras"
    result = parser.parse_line(line)

    assert result == "SUMMARY_START"
    assert parser.stats_found


def test_parse_line_known_error(parser):
    """Test parsing an error line with a known Windows error code."""
    line = "2023/10/24 10:00:00 ERROR 5 (0x00000005) Accessing Destination Directory C:\\Dest\\"
    result = parser.parse_line(line)

    _t = "Error 5 (Access Denied): 2023/10/24 10:00:00 ERROR 5 (0x00000005) Accessing Destination Directory C:\\Dest\\"
    assert result == _t


def test_parse_line_unknown_error(parser):
    """Test parsing an error line with an unknown Windows error code."""
    line = "2023/10/24 10:00:00 ERROR 999 (0x000003E7) Something went wrong"
    result = parser.parse_line(line)

    assert result == "Error 999 (Unknown Error): 2023/10/24 10:00:00 ERROR 999 (0x000003E7) Something went wrong"
