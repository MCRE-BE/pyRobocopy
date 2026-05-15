from pathlib import Path

from robocopy.config import RobocopyConfig
from robocopy.types import RobocopyResult


def test_robocopy_result_success():
    """Verify that success property correctly identifies successful exit codes."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))

    # Exit codes 0-7 are success
    for code in range(8):
        result = RobocopyResult(config=config, exit_code=code)
        assert result.success is True, f"Exit code {code} should be successful"

    # Exit codes 8+ are failure
    for code in range(8, 17):
        result = RobocopyResult(config=config, exit_code=code)
        assert result.success is False, f"Exit code {code} should be failure"
