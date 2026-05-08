from robocopy.config import RobocopyConfig


def test_from_command_line_windows_paths():
    # Test that backslashes in paths are not treated as escape characters
    cmd = r"robocopy C:\Temp\Source D:\Dest"
    config = RobocopyConfig.from_command_line(cmd)

    assert str(config.source) == r"C:\Temp\Source"
    assert str(config.destination) == r"D:\Dest"


def test_from_command_line_quoted_windows_paths():
    # Test that quoted paths with spaces and backslashes are parsed correctly
    cmd = r'robocopy "C:\Path With Spaces" "D:\Dest Path"'
    config = RobocopyConfig.from_command_line(cmd)

    assert str(config.source) == r"C:\Path With Spaces"
    assert str(config.destination) == r"D:\Dest Path"


def test_from_command_line_quoted_command():
    # Test that quoted command name is accepted
    cmd = r'"robocopy" src dst'
    config = RobocopyConfig.from_command_line(cmd)
    assert str(config.source) == "src"
    assert str(config.destination) == "dst"


def test_from_command_line_single_quoted_paths():
    # Test that single quoted paths are parsed correctly (shlex non-posix supports this)
    cmd = r"robocopy 'C:\Source' 'D:\Dest'"
    config = RobocopyConfig.from_command_line(cmd)
    assert str(config.source) == r"C:\Source"
    assert str(config.destination) == r"D:\Dest"
