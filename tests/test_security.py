"""Security tests."""

####################
# IMPORT STATEMENT #
####################
from pathlib import Path

import pytest

from robocopy.config import RobocopyConfig


#########
# TESTS #
#########
def test_validate_valid_config():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    # Should not raise
    config.validate()
    assert config.to_args()[1:3] == ["src", "dst"]


def test_validate_empty_source():
    config = RobocopyConfig(source=Path(""), destination=Path("dst"))
    with pytest.raises(ValueError, match="source path cannot be empty"):
        config.to_args()


def test_validate_empty_destination():
    config = RobocopyConfig(source=Path("src"), destination=Path(""))
    with pytest.raises(ValueError, match="destination path cannot be empty"):
        config.to_args()


def test_validate_null_byte_in_source():
    config = RobocopyConfig(source=Path("src\0bad"), destination=Path("dst"))
    with pytest.raises(ValueError, match="source path contains invalid characters"):
        config.to_args()


def test_validate_newline_in_destination():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst\nmore"))
    with pytest.raises(ValueError, match="destination path contains invalid characters"):
        config.to_args()


def test_validate_null_byte_in_files():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"), files="*.*\0")
    with pytest.raises(ValueError, match="File filter contains invalid characters"):
        config.to_args()


def test_validate_null_byte_in_exclude_files():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    config.selection.exclude_files = ["fine.txt", "bad\0.txt"]
    with pytest.raises(ValueError, match=r"exclude_files item 'bad\x00.txt' contains invalid characters"):
        config.to_args()


def test_validate_newline_in_exclude_dirs():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    config.selection.exclude_dirs = ["dir\n1", "dir2"]
    with pytest.raises(ValueError, match="exclude_dirs item 'dir\n1' contains invalid characters"):
        config.to_args()


def test_validate_slash_in_source():
    config = RobocopyConfig(source="/MIR", destination=Path("dst"))
    with pytest.raises(ValueError, match="source path cannot start with '/' to prevent argument injection"):
        config.to_args()


def test_validate_slash_in_destination():
    config = RobocopyConfig(source=Path("src"), destination="/PURGE")
    with pytest.raises(ValueError, match="destination path cannot start with '/' to prevent argument injection"):
        config.to_args()


def test_validate_slash_in_files():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"), files="/MIR")
    with pytest.raises(ValueError, match="File filter cannot start with '/' to prevent argument injection"):
        config.to_args()


def test_validate_slash_in_exclude_files():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    config.selection.exclude_files = ["fine.txt", "/PURGE"]
    with pytest.raises(
        ValueError, match=r"exclude_files item '/PURGE' cannot start with '/' to prevent argument injection"
    ):
        config.to_args()


def test_validate_slash_in_exclude_dirs():
    config = RobocopyConfig(source=Path("src"), destination=Path("dst"))
    config.selection.exclude_dirs = ["/MIR", "dir2"]
    with pytest.raises(
        ValueError, match=r"exclude_dirs item '/MIR' cannot start with '/' to prevent argument injection"
    ):
        config.to_args()
