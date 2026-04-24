import sys
from unittest.mock import MagicMock

# Mock tqdm
sys.modules["tqdm"] = MagicMock()
sys.modules["tqdm.auto"] = MagicMock()
