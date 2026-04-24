# %%
####################
# Import Statement #
####################
import sys
import threading
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


def test_runner_no_deadlock_on_stderr_flood():
    """Verify that RobocopyRunner does not deadlock when stderr is flooded."""
    # Script that writes a lot to stderr and then some to stdout
    code = """
import sys
# Write 100KB to stderr
sys.stderr.write('E' * 1024 * 100)
sys.stderr.flush()
# Write something to stdout
sys.stdout.write('DONE\\n')
sys.stdout.flush()
"""

    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    runner = RobocopyRunner(config=config)

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch.object(RobocopyConfig, "to_args", return_value=[sys.executable, "-c", code]),
    ):
        # We use a thread to run it so we can timeout if it deadlocks
        result_container = []

        def run_it():
            try:
                res = runner.run()
                result_container.append(res)
            except Exception as e:
                result_container.append(e)

        thread = threading.Thread(target=run_it)
        thread.start()

        thread.join(timeout=5)
        assert not thread.is_alive(), "RobocopyRunner.run() deadlocked!"

        res = result_container[0]
        assert not isinstance(res, Exception), f"Runner raised exception: {res}"
        assert res.exit_code == 0
