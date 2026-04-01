__doc__ = """A module containing a quick way to copy files."""
__all__ = [
    "robocopy",
    "RobocopyError",
]

# %%
####################
# Import statement #
####################
from .core import robocopy, RobocopyError
