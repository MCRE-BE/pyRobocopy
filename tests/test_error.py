from robocopy.error import NothingToLoadError, RobocopyError


def test_robocopy_error_is_exception():
    """Test that RobocopyError subclasses Exception."""
    assert issubclass(RobocopyError, Exception)


def test_nothing_to_load_error_is_exception():
    """Test that NothingToLoadError subclasses Exception."""
    assert issubclass(NothingToLoadError, Exception)


def test_robocopy_error_instantiation():
    """Test that RobocopyError can be instantiated with a message."""
    error = RobocopyError("An error occurred")
    assert isinstance(error, RobocopyError)
    assert isinstance(error, Exception)
    assert str(error) == "An error occurred"


def test_nothing_to_load_error_instantiation():
    """Test that NothingToLoadError can be instantiated with a message."""
    error = NothingToLoadError("Nothing to load")
    assert isinstance(error, NothingToLoadError)
    assert isinstance(error, Exception)
    assert str(error) == "Nothing to load"
