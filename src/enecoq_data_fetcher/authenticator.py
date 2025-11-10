"""Authentication component for enecoQ web service."""

from playwright.sync_api import Page

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger


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

    def __init__(self, email: str, password: str, user_agent: str = None):
        """Initialize authenticator with credentials.
        
        Args:
            email: User's email address for enecoQ login.
            password: User's password for enecoQ login.
            user_agent: Optional user agent string for HTTP requests.
        """
        self._email = email
        self._password = password
        self._user_agent = user_agent
        self._log = logger.get_logger()

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
            self._log.debug(f"Navigating to login page: {self.LOGIN_URL}")
            page.goto(self.LOGIN_URL, wait_until="networkidle")
            
            # Fill in email
            self._log.debug("Locating email input field")
            email_input = page.locator(self.EMAIL_SELECTOR)
            if not email_input.is_visible():
                self._log.error("Login form not found on page")
                raise exceptions.AuthenticationError(
                    "Login form not found on page"
                )
            self._log.debug("Filling email field")
            email_input.fill(self._email)
            
            # Fill in password (DO NOT log password value)
            self._log.debug("Filling password field")
            password_input = page.locator(self.PASSWORD_SELECTOR)
            password_input.fill(self._password)
            
            # Submit the form
            self._log.debug("Submitting login form")
            submit_button = page.locator(self.SUBMIT_SELECTOR)
            submit_button.click()
            
            # Wait for navigation after login
            self._log.debug("Waiting for page load after login")
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
                
                self._log.error(error_msg)
                raise exceptions.AuthenticationError(error_msg)
            
            self._log.info("Login successful")
                
        except exceptions.AuthenticationError:
            # Re-raise authentication errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in AuthenticationError
            self._log.error(f"Login failed due to unexpected error: {str(e)}", exc_info=True)
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
            is_logged_in = logout_link.count() > 0
            self._log.debug(f"Login status check: {is_logged_in}")
            return is_logged_in
        except Exception as e:
            # If any error occurs during check, assume not logged in
            self._log.debug(f"Login status check failed: {e}")
            return False
