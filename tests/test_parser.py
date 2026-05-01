import pytest
from unittest.mock import MagicMock

from robocopy.parser import RobocopyParser
from robocopy.config import RobocopyConfig

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

def test_parse_line_regular(parser):
    """Test that a regular line returns the stripped line."""
    line = "  New File  \t\t 12345  file.txt  "
    assert parser.parse_line(line) == "New File  \t\t 12345  file.txt"

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

    assert result == "Error 5 (Access Denied): 2023/10/24 10:00:00 ERROR 5 (0x00000005) Accessing Destination Directory C:\\Dest\\"

def test_parse_line_unknown_error(parser):
    """Test parsing an error line with an unknown Windows error code."""
    line = "2023/10/24 10:00:00 ERROR 999 (0x000003E7) Something went wrong"
    result = parser.parse_line(line)

    assert result == "Error 999 (Unknown Error): 2023/10/24 10:00:00 ERROR 999 (0x000003E7) Something went wrong"
