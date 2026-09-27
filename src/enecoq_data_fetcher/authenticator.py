"""Authentication component for enecoQ web service."""

from playwright import sync_api

from enecoq_data_fetcher import exceptions, logger


class EnecoQAuthenticator:
    """Handles authentication with enecoQ web service."""

    # CYBERHOME login page URL
    LOGIN_URL = "https://www.cyberhome.ne.jp/app/sslLogin.do"

    # Selectors for login form elements
    EMAIL_SELECTOR = 'input[name="user_id"]'
    PASSWORD_SELECTOR = 'input[name="password"]'
    SUBMIT_SELECTOR = 'button[type="submit"]'

    # The logout link uses href="#" with onclick, so it is found by its text.
    LOGGED_IN_INDICATOR = 'a:has-text("ログアウト")'
    ERROR_MESSAGE_SELECTOR = '.error, .alert, [class*="error"]'

    def __init__(self, email: str, password: str) -> None:
        """Initialize authenticator with credentials.

        Args:
            email: User's email address for enecoQ login.
            password: User's password for enecoQ login.
        """
        self._email = email
        self._password = password
        self._log = logger.get_logger()

    def login(self, page: sync_api.Page) -> None:
        """Log in to the CYBERHOME site that hosts enecoQ.

        Session cookies are kept by the page's browser context.

        Args:
            page: Playwright page to log in with.

        Raises:
            AuthenticationError: If the login form is missing or the
                credentials are rejected. These are not retried.
            playwright.sync_api.Error: If the browser fails, including
                timeouts. The controller retries these.
        """
        self._log.debug("Navigating to login page: %s", self.LOGIN_URL)
        page.goto(self.LOGIN_URL, wait_until="networkidle")

        email_input = page.locator(self.EMAIL_SELECTOR)
        if not email_input.is_visible():
            raise exceptions.AuthenticationError("Login form not found on page")
        email_input.fill(self._email)
        page.locator(self.PASSWORD_SELECTOR).fill(self._password)

        self._log.debug("Submitting login form")
        page.locator(self.SUBMIT_SELECTOR).click()
        page.wait_for_load_state("networkidle")

        if not self.is_logged_in(page):
            raise exceptions.AuthenticationError(self._failure_message(page))
        self._log.info("Login successful")

    def is_logged_in(self, page: sync_api.Page) -> bool:
        """Check whether the page shows the logged-in state.

        Args:
            page: Playwright page to check.

        Returns:
            True if the logout link is present, False otherwise.
        """
        try:
            is_logged_in = page.locator(self.LOGGED_IN_INDICATOR).count() > 0
        except sync_api.Error as e:
            self._log.debug("Login status check failed: %s", e)
            return False
        self._log.debug("Login status check: %s", is_logged_in)
        return is_logged_in

    def _failure_message(self, page: sync_api.Page) -> str:
        """Build the error message for a rejected login.

        Args:
            page: Playwright page showing the login result.

        Returns:
            Error message, including the page's error text if there is one.
        """
        error_elements = page.locator(self.ERROR_MESSAGE_SELECTOR)
        if error_elements.count() > 0:
            error_text = error_elements.first.text_content()
            if error_text:
                return f"Authentication failed: {error_text.strip()}"
        return "Authentication failed"
