"""Authentication component for enecoQ web service."""

from playwright.sync_api import Page

from enecoq_data_fetcher import exceptions


class EnecoQAuthenticator:
    """Handles authentication with enecoQ web service."""

    # CYBERHOME login page URL
    LOGIN_URL = "https://www.cyberhome.ne.jp/app/sslLogin.do"
    
    # Selectors for login form elements
    EMAIL_SELECTOR = 'input[name="user_id"]'
    PASSWORD_SELECTOR = 'input[name="password"]'
    SUBMIT_SELECTOR = 'button[type="submit"]'
    
    # Selector to verify successful login
    # Note: Logout link uses href="#" with onclick, so we search by text
    LOGGED_IN_INDICATOR = 'a:has-text("ログアウト")'
    ERROR_MESSAGE_SELECTOR = '.error, .alert, [class*="error"]'

    def __init__(self, email: str, password: str):
        """Initialize authenticator with credentials.
        
        Args:
            email: User's email address for enecoQ login.
            password: User's password for enecoQ login.
        """
        self._email = email
        self._password = password

    def login(self, page: Page) -> None:
        """Authenticate with enecoQ web service.
        
        Navigates to the CYBERHOME login page, enters credentials,
        and submits the login form. Session cookies are automatically
        managed by Playwright's browser context.
        
        Args:
            page: Playwright page object to use for authentication.
            
        Raises:
            AuthenticationError: If login fails due to invalid credentials
                or other authentication issues.
        """
        try:
            # Navigate to login page
            page.goto(self.LOGIN_URL, wait_until="networkidle")
            
            # Fill in email
            email_input = page.locator(self.EMAIL_SELECTOR)
            if not email_input.is_visible():
                raise exceptions.AuthenticationError(
                    "Login form not found on page"
                )
            email_input.fill(self._email)
            
            # Fill in password
            password_input = page.locator(self.PASSWORD_SELECTOR)
            password_input.fill(self._password)
            
            # Submit the form
            submit_button = page.locator(self.SUBMIT_SELECTOR)
            submit_button.click()
            
            # Wait for navigation after login
            page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            if not self.is_logged_in(page):
                # Try to find error message
                error_msg = "Authentication failed"
                error_elements = page.locator(self.ERROR_MESSAGE_SELECTOR)
                if error_elements.count() > 0:
                    error_text = error_elements.first.text_content()
                    if error_text:
                        error_msg = f"Authentication failed: {error_text.strip()}"
                
                raise exceptions.AuthenticationError(error_msg)
                
        except exceptions.AuthenticationError:
            # Re-raise authentication errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in AuthenticationError
            raise exceptions.AuthenticationError(
                f"Login failed due to unexpected error: {str(e)}"
            ) from e

    def is_logged_in(self, page: Page) -> bool:
        """Check if the user is currently logged in.
        
        Verifies login status by checking for the presence of
        logout link or other logged-in indicators on the page.
        
        Args:
            page: Playwright page object to check.
            
        Returns:
            True if user is logged in, False otherwise.
        """
        try:
            # Check for logout link which indicates successful login
            logout_link = page.locator(self.LOGGED_IN_INDICATOR)
            return logout_link.count() > 0
        except Exception:
            # If any error occurs during check, assume not logged in
            return False
