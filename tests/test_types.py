from unittest.mock import MagicMock

import pytest

from robocopy.types import RobocopyResult


@pytest.mark.parametrize(
    ("exit_code", "expected_success"),
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, False),
        (9, False),
        (16, False),
    ],
)
def test_robocopyresult_success(exit_code, expected_success):
    """Test that the RobocopyResult.success property computes correctly based on exit_code."""
    mock_config = MagicMock()
    result = RobocopyResult(config=mock_config, exit_code=exit_code)
    assert result.success is expected_success
