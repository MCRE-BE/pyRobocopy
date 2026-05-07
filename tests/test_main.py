import sys
from unittest.mock import patch

from robocopy.__main__ import main


def test_main_run():
    with patch.object(sys, "argv", ["pyrobocopy", "help"]):
        import contextlib
        with contextlib.suppress(SystemExit):
            main()

def test_main_direct():
    with patch("robocopy.__main__.main") as _, patch.dict("sys.modules", {"robocopy.__main__": None}):
        # Simulate import side effects? No, we just need coverage on `if __name__ == "__main__": main()`
        pass

# To get __name__ == '__main__' coverage:
def test_main_execution():
    import runpy
    import sys
    from unittest.mock import patch

    import pytest
    with patch.object(sys, "argv", ["pyrobocopy", "help"]), pytest.raises(SystemExit):
        runpy.run_module("robocopy.__main__", run_name="__main__")
