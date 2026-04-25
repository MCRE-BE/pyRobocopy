import sys
from unittest.mock import MagicMock

# Mock tqdm if it's not installed
try:
    import tqdm  # noqa: F401
except ImportError:
    mock_tqdm = MagicMock()
    sys.modules["tqdm"] = mock_tqdm
    sys.modules["tqdm.auto"] = mock_tqdm
