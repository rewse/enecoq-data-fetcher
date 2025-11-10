"""Tests for authenticator component."""

from unittest.mock import Mock, patch

from enecoq_data_fetcher import authenticator
from enecoq_data_fetcher import exceptions


def test_authenticator_initialization():
    """Test authenticator initialization."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    assert auth._email == "test@example.com"
    assert auth._password == "test123"
    print("✓ Authenticator initialization test passed")


def test_authenticator_with_user_agent():
    """Test authenticator initialization with custom user agent."""
    custom_ua = "Custom User Agent"
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123",
        user_agent=custom_ua
    )
    
    assert auth._user_agent == custom_ua
    print("✓ Authenticator with user agent test passed")


def test_login_success():
    """Test successful login."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    # Create mock page
    mock_page = Mock()
    mock_email_input = Mock()
    mock_password_input = Mock()
    mock_submit_button = Mock()
    mock_logout_link = Mock()
    
    # Setup mock behavior
    mock_page.locator.side_effect = lambda selector: {
        'input[name="user_id"]': mock_email_input,
        'input[name="password"]': mock_password_input,
        'button[type="submit"]': mock_submit_button,
        'a:has-text("ログアウト")': mock_logout_link,
    }.get(selector, Mock())
    
    mock_email_input.is_visible.return_value = True
    mock_logout_link.count.return_value = 1  # Logged in
    
    # Execute login
    auth.login(mock_page)
    
    # Verify calls
    mock_page.goto.assert_called_once()
    mock_email_input.fill.assert_called_once_with("test@example.com")
    mock_password_input.fill.assert_called_once_with("test123")
    mock_submit_button.click.assert_called_once()
    
    print("✓ Login success test passed")


def test_login_form_not_found():
    """Test login when form is not found."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    # Create mock page
    mock_page = Mock()
    mock_email_input = Mock()
    
    # Setup mock behavior - form not visible
    mock_page.locator.return_value = mock_email_input
    mock_email_input.is_visible.return_value = False
    
    # Execute login and expect error
    try:
        auth.login(mock_page)
        assert False, "Should have raised AuthenticationError"
    except exceptions.AuthenticationError as e:
        assert "Login form not found" in str(e)
    
    print("✓ Login form not found test passed")


def test_login_authentication_failed():
    """Test login when authentication fails."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="wrong"
    )
    
    # Create mock page
    mock_page = Mock()
    mock_email_input = Mock()
    mock_password_input = Mock()
    mock_submit_button = Mock()
    mock_logout_link = Mock()
    mock_error_element = Mock()
    
    # Setup mock behavior
    def locator_side_effect(selector):
        if selector == 'input[name="user_id"]':
            return mock_email_input
        elif selector == 'input[name="password"]':
            return mock_password_input
        elif selector == 'button[type="submit"]':
            return mock_submit_button
        elif selector == 'a:has-text("ログアウト")':
            return mock_logout_link
        elif selector == '.error, .alert, [class*="error"]':
            return mock_error_element
        return Mock()
    
    mock_page.locator.side_effect = locator_side_effect
    
    mock_email_input.is_visible.return_value = True
    mock_logout_link.count.return_value = 0  # Not logged in
    mock_error_element.count.return_value = 0  # No error message
    
    # Execute login and expect error
    try:
        auth.login(mock_page)
        assert False, "Should have raised AuthenticationError"
    except exceptions.AuthenticationError as e:
        assert "Authentication failed" in str(e)
    
    print("✓ Login authentication failed test passed")


def test_login_with_error_message():
    """Test login failure with error message on page."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="wrong"
    )
    
    # Create mock page
    mock_page = Mock()
    mock_email_input = Mock()
    mock_password_input = Mock()
    mock_submit_button = Mock()
    mock_logout_link = Mock()
    mock_error_element = Mock()
    
    # Setup mock behavior
    def locator_side_effect(selector):
        if selector == 'input[name="user_id"]':
            return mock_email_input
        elif selector == 'input[name="password"]':
            return mock_password_input
        elif selector == 'button[type="submit"]':
            return mock_submit_button
        elif selector == 'a:has-text("ログアウト")':
            return mock_logout_link
        elif selector == '.error, .alert, [class*="error"]':
            return mock_error_element
        return Mock()
    
    mock_page.locator.side_effect = locator_side_effect
    
    mock_email_input.is_visible.return_value = True
    mock_logout_link.count.return_value = 0  # Not logged in
    mock_error_element.count.return_value = 1
    mock_error_element.first.text_content.return_value = "Invalid credentials"
    
    # Execute login and expect error
    try:
        auth.login(mock_page)
        assert False, "Should have raised AuthenticationError"
    except exceptions.AuthenticationError as e:
        assert "Invalid credentials" in str(e)
    
    print("✓ Login with error message test passed")


def test_login_unexpected_error():
    """Test login with unexpected error."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    # Create mock page that raises exception
    mock_page = Mock()
    mock_page.goto.side_effect = Exception("Network error")
    
    # Execute login and expect wrapped error
    try:
        auth.login(mock_page)
        assert False, "Should have raised AuthenticationError"
    except exceptions.AuthenticationError as e:
        assert "unexpected error" in str(e)
        assert "Network error" in str(e)
    
    print("✓ Login unexpected error test passed")


def test_is_logged_in_true():
    """Test is_logged_in when user is logged in."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    # Create mock page
    mock_page = Mock()
    mock_logout_link = Mock()
    mock_logout_link.count.return_value = 1
    mock_page.locator.return_value = mock_logout_link
    
    # Check login status
    result = auth.is_logged_in(mock_page)
    
    assert result is True
    print("✓ is_logged_in true test passed")


def test_is_logged_in_false():
    """Test is_logged_in when user is not logged in."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    # Create mock page
    mock_page = Mock()
    mock_logout_link = Mock()
    mock_logout_link.count.return_value = 0
    mock_page.locator.return_value = mock_logout_link
    
    # Check login status
    result = auth.is_logged_in(mock_page)
    
    assert result is False
    print("✓ is_logged_in false test passed")


def test_is_logged_in_error():
    """Test is_logged_in when error occurs."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    # Create mock page that raises exception
    mock_page = Mock()
    mock_page.locator.side_effect = Exception("Page error")
    
    # Check login status - should return False on error
    result = auth.is_logged_in(mock_page)
    
    assert result is False
    print("✓ is_logged_in error test passed")


def test_login_url_constant():
    """Test LOGIN_URL constant."""
    assert authenticator.EnecoQAuthenticator.LOGIN_URL == "https://www.cyberhome.ne.jp/app/sslLogin.do"
    print("✓ LOGIN_URL constant test passed")


def test_selector_constants():
    """Test selector constants."""
    assert authenticator.EnecoQAuthenticator.EMAIL_SELECTOR == 'input[name="user_id"]'
    assert authenticator.EnecoQAuthenticator.PASSWORD_SELECTOR == 'input[name="password"]'
    assert authenticator.EnecoQAuthenticator.SUBMIT_SELECTOR == 'button[type="submit"]'
    assert authenticator.EnecoQAuthenticator.LOGGED_IN_INDICATOR == 'a:has-text("ログアウト")'
    print("✓ Selector constants test passed")


if __name__ == "__main__":
    print("Running authenticator tests...\n")
    
    test_authenticator_initialization()
    test_authenticator_with_user_agent()
    test_login_success()
    test_login_form_not_found()
    test_login_authentication_failed()
    test_login_with_error_message()
    test_login_unexpected_error()
    test_is_logged_in_true()
    test_is_logged_in_false()
    test_is_logged_in_error()
    test_login_url_constant()
    test_selector_constants()
    
    print("\n✓ All authenticator tests passed!")
