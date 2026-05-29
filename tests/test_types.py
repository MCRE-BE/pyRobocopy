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


def test_robocopy_status_counts_towards_total():
    """Verify RobocopyStatus.counts_towards_total for all status values."""
    from robocopy.types import RobocopyStatus

    # Should count towards total
    assert RobocopyStatus.NEW_FILE.counts_towards_total is True
    assert RobocopyStatus.NEWER.counts_towards_total is True
    assert RobocopyStatus.OLDER.counts_towards_total is True
    assert RobocopyStatus.SAME.counts_towards_total is True
    assert RobocopyStatus.MISMATCH.counts_towards_total is True
    assert RobocopyStatus.MODIFIED.counts_towards_total is True
    assert RobocopyStatus.TWEAKED.counts_towards_total is True
    assert RobocopyStatus.FAILED.counts_towards_total is True
    assert RobocopyStatus.LONELY.counts_towards_total is True

    # Should NOT count towards total
    assert RobocopyStatus.NEW_DIR.counts_towards_total is False
    assert RobocopyStatus.EXTRA_FILE.counts_towards_total is False
    assert RobocopyStatus.EXTRA_DIR.counts_towards_total is False
    assert RobocopyStatus.UNKNOWN.counts_towards_total is False
