"""Exceptions for the Robocopy library."""


class NothingToLoadError(Exception):
    """Raised when the source directory is empty or does not exist."""


class RobocopyError(Exception):
    """Base exception for Robocopy errors."""
