from unittest.mock import patch
import sys
from robocopy.__main__ import main

def test_main_run():
    with patch.object(sys, "argv", ["pyrobocopy", "help"]):
        try:
            main()
        except SystemExit:
            pass

def test_main_direct():
    with patch("robocopy.__main__.main") as mock_main:
        with patch.dict("sys.modules", {"robocopy.__main__": None}):
            # Simulate import side effects? No, we just need coverage on `if __name__ == "__main__": main()`
            pass

# To get __name__ == '__main__' coverage:
def test_main_execution():
    import runpy
    import pytest
    import sys
    from unittest.mock import patch
    with patch.object(sys, "argv", ["pyrobocopy", "help"]):
        with pytest.raises(SystemExit):
            runpy.run_module("robocopy.__main__", run_name="__main__")
