# %%
####################
# Import Statement #
####################
from pathlib import Path
from unittest.mock import MagicMock, patch

from robocopy import RobocopyConfig, RobocopyRunner


#########
# TESTS #
#########
def test_discover_totals_arguments():
    """Verify that discover_totals uses the expected optimization flags."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    mock_stdout = """
-------------------------------------------------------------------------------
   ROBOCOPY     ::     Robust File Copy for Windows
-------------------------------------------------------------------------------

               Total    Copied   Skipped  Mismatch    FAILED    Extras
    Dirs :         1         0         1         0         0         0
   Files :        10         0        10         0         0         0
   Bytes :       100         0       100         0         0         0
   Times :   0:00:00   0:00:00                       0:00:00   0:00:00
"""

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)

        total = runner.discover_totals()

        assert total == 10
        args = mock_run.call_args[0][0]

        assert "/NFL" in args
        assert "/NDL" in args
        assert "/L" in args
        assert "/NJH" in args
        assert "/MT:32" in args


def test_discover_totals_includes_optimization_flags():
    """Specifically check for the new optimization flags."""
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Files : 5", returncode=0)
        runner.discover_totals()
        args = mock_run.call_args[0][0]

        assert "/NFL" in args
        assert "/NDL" in args
