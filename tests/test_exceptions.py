"""Tests for custom exceptions."""

from enecoq_data_fetcher import exceptions


def test_enecoq_error_basic():
    """Test basic EnecoQError creation."""
    error = exceptions.EnecoQError("Test error")
    
    assert error.message == "Test error"
    assert error.error_code is None
    assert str(error) == "Test error"
    print("✓ EnecoQError basic test passed")


def test_enecoq_error_with_code():
    """Test EnecoQError with error code."""
    error = exceptions.EnecoQError("Test error", "TEST_CODE")
    
    assert error.message == "Test error"
    assert error.error_code == "TEST_CODE"
    assert str(error) == "[TEST_CODE] Test error"
    print("✓ EnecoQError with code test passed")


def test_authentication_error_default():
    """Test AuthenticationError with default message."""
    error = exceptions.AuthenticationError()
    
    assert error.message == "Authentication failed"
    assert error.error_code == "AUTH_ERROR"
    assert str(error) == "[AUTH_ERROR] Authentication failed"
    print("✓ AuthenticationError default test passed")


def test_authentication_error_custom():
    """Test AuthenticationError with custom message."""
    error = exceptions.AuthenticationError("Invalid credentials", "INVALID_CREDS")
    
    assert error.message == "Invalid credentials"
    assert error.error_code == "INVALID_CREDS"
    assert str(error) == "[INVALID_CREDS] Invalid credentials"
    print("✓ AuthenticationError custom test passed")


def test_fetch_error_default():
    """Test FetchError with default message."""
    error = exceptions.FetchError()
    
    assert error.message == "Data fetch failed"
    assert error.error_code == "FETCH_ERROR"
    assert str(error) == "[FETCH_ERROR] Data fetch failed"
    print("✓ FetchError default test passed")


def test_fetch_error_custom():
    """Test FetchError with custom message."""
    error = exceptions.FetchError("Network timeout", "TIMEOUT")
    
    assert error.message == "Network timeout"
    assert error.error_code == "TIMEOUT"
    assert str(error) == "[TIMEOUT] Network timeout"
    print("✓ FetchError custom test passed")


def test_export_error_default():
    """Test ExportError with default message."""
    error = exceptions.ExportError()
    
    assert error.message == "Data export failed"
    assert error.error_code == "EXPORT_ERROR"
    assert str(error) == "[EXPORT_ERROR] Data export failed"
    print("✓ ExportError default test passed")


def test_export_error_custom():
    """Test ExportError with custom message."""
    error = exceptions.ExportError("File write error", "FILE_ERROR")
    
    assert error.message == "File write error"
    assert error.error_code == "FILE_ERROR"
    assert str(error) == "[FILE_ERROR] File write error"
    print("✓ ExportError custom test passed")


def test_exception_inheritance():
    """Test exception inheritance hierarchy."""
    # All custom exceptions should inherit from EnecoQError
    assert issubclass(exceptions.AuthenticationError, exceptions.EnecoQError)
    assert issubclass(exceptions.FetchError, exceptions.EnecoQError)
    assert issubclass(exceptions.ExportError, exceptions.EnecoQError)
    
    # All should also inherit from Exception
    assert issubclass(exceptions.EnecoQError, Exception)
    assert issubclass(exceptions.AuthenticationError, Exception)
    assert issubclass(exceptions.FetchError, Exception)
    assert issubclass(exceptions.ExportError, Exception)
    
    print("✓ Exception inheritance test passed")


def test_exception_catching():
    """Test catching exceptions."""
    # Test catching specific exception
    try:
        raise exceptions.AuthenticationError("Test")
    except exceptions.AuthenticationError as e:
        assert e.message == "Test"
    
    # Test catching base exception
    try:
        raise exceptions.FetchError("Test")
    except exceptions.EnecoQError as e:
        assert e.message == "Test"
    
    # Test catching all exceptions
    try:
        raise exceptions.ExportError("Test")
    except Exception as e:
        assert isinstance(e, exceptions.EnecoQError)
    
    print("✓ Exception catching test passed")


def test_exception_raising():
    """Test raising and catching exceptions."""
    # Test AuthenticationError
    try:
        raise exceptions.AuthenticationError("Login failed")
    except exceptions.AuthenticationError as e:
        assert "Login failed" in str(e)
    else:
        assert False, "Exception not raised"
    
    # Test FetchError
    try:
        raise exceptions.FetchError("Network error")
    except exceptions.FetchError as e:
        assert "Network error" in str(e)
    else:
        assert False, "Exception not raised"
    
    # Test ExportError
    try:
        raise exceptions.ExportError("Write error")
    except exceptions.ExportError as e:
        assert "Write error" in str(e)
    else:
        assert False, "Exception not raised"
    
    print("✓ Exception raising test passed")


def test_exception_chaining():
    """Test exception chaining with from clause."""
    original_error = ValueError("Original error")
    
    try:
        try:
            raise original_error
        except ValueError as e:
            raise exceptions.FetchError("Wrapped error") from e
    except exceptions.FetchError as e:
        assert e.message == "Wrapped error"
        assert e.__cause__ == original_error
    
    print("✓ Exception chaining test passed")


if __name__ == "__main__":
    print("Running exception tests...\n")
    
    test_enecoq_error_basic()
    test_enecoq_error_with_code()
    test_authentication_error_default()
    test_authentication_error_custom()
    test_fetch_error_default()
    test_fetch_error_custom()
    test_export_error_default()
    test_export_error_custom()
    test_exception_inheritance()
    test_exception_catching()
    test_exception_raising()
    test_exception_chaining()
    
    print("\n✓ All exception tests passed!")
