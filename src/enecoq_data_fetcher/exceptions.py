"""Custom exceptions for enecoQ data fetcher."""


class EnecoQError(Exception):
    """Base exception for enecoQ tool.

    All custom exceptions in this package inherit from this base class.
    This allows catching all enecoQ-specific errors with a single except clause.

    Attributes:
        message: Human-readable error message.
        error_code: Optional error code for programmatic error handling.
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            error_code: Optional error code for programmatic error handling.
        """
        self.message = message
        self.error_code = error_code
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(EnecoQError):
    """Authentication failed.

    Raised when login to enecoQ Web Service fails due to invalid credentials,
    session expiration, or other authentication-related issues.
    """

    def __init__(
        self, message: str = "Authentication failed", error_code: str = "AUTH_ERROR"
    ) -> None:
        """Initialize the authentication error.

        Args:
            message: Human-readable error message.
            error_code: Error code for authentication failures.
        """
        super().__init__(message, error_code)


class FetchError(EnecoQError):
    """Data fetch failed.

    Raised when data retrieval from enecoQ Web Service fails due to network
    issues, server errors, or unexpected response format.
    """

    def __init__(
        self, message: str = "Data fetch failed", error_code: str = "FETCH_ERROR"
    ) -> None:
        """Initialize the fetch error.

        Args:
            message: Human-readable error message.
            error_code: Error code for fetch failures.
        """
        super().__init__(message, error_code)


class ExportError(EnecoQError):
    """Data export failed.

    Raised when exporting data to file or console fails due to I/O errors,
    permission issues, or formatting problems.
    """

    def __init__(
        self, message: str = "Data export failed", error_code: str = "EXPORT_ERROR"
    ) -> None:
        """Initialize the export error.

        Args:
            message: Human-readable error message.
            error_code: Error code for export failures.
        """
        super().__init__(message, error_code)
