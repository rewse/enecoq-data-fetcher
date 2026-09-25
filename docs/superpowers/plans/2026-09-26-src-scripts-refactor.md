# src/ と scripts/ のリファクター実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `src/enecoq_data_fetcher/` と `scripts/` のバグを直し、重複と未使用コードを整理する。

**Architecture:** モジュール構成（`cli` → `controller` → `authenticator` / `fetcher` → `exporter`、補助の `config` / `logger` / `models` / `exceptions`）は変えず、各モジュールの中身を直す。依存の少ない `config` と `logger` から始め、`authenticator` → `fetcher` → `controller` → `cli` の順に進め、最後にテストランナー、リリーススクリプト、ドキュメントを直す。

**Tech Stack:** Python 3.10 以上、Click、Playwright（`playwright.sync_api`）、PyYAML、uv、bash

**Spec:** `docs/superpowers/specs/2026-09-26-src-scripts-refactor-design.md`

## Global Constraints

- サポートする Python は `requires-python = ">=3.10"`。3.10 で使えない構文を使わない
- Google Python Style Guide に従い、import はモジュール単位にする（`typing`、`collections.abc` からの型は例外）。1 行 80 文字以内
- ログは `log.info("... %s", value)` の形で引数を渡し、f-string を使わない
- 標準出力、JSON、単位の表記は英語にする（`JPY`、`kWh`、`kg`）
- JSON のキー（`period`、`timestamp`、`usage`、`cost`、`co2`）は変えない
- 終了コード: 1 認証、2 取得、3 出力、4 その他の enecoQ エラー、5 想定外、6 引数と設定
- 新しい依存は PyYAML（`pyyaml>=6.0.3`、作業ツリーで追加済み）だけにする
- テストは pytest ではなく、各ファイルの `if __name__ == "__main__":` から実行する。新しいテスト関数はそのブロックにも追加する
- テストの実行は `PYTHONPATH=src uv run python tests/<file>.py`。関数単位では `PYTHONPATH=src uv run python -c "from tests import test_x as t; t.test_y()"`
- コミットメッセージは Conventional Commits で、スコープはモジュール名、本文に理由を書く

## Review Focus

- enecoQ のウィジェットがデータ準備中に `--kWh` のような数字のない表示を出したとき、0 ではなく `FetchError` になること（Task 4 でテスト）
- 例外メッセージにパスワードが含まれても、ログファイルには `****` として書かれること（Task 6 でテスト）
- `--config` を付けずに実行したとき、カレントディレクトリに `config.yaml` があれば読み、なければデフォルトで動くこと（Task 6 でテスト）
- ログイン中の `sync_api.TimeoutError` がリトライされること（Task 5 でテスト）
- 未追跡ファイルがある、または push していないコミットがある状態でリリースしようとしたとき、何も変更せずに止まること（Task 7 でテスト）

---

### Task 1: config の検証と PyYAML の必須化

**Files:**
- Modify: `src/enecoq_data_fetcher/config.py`（全体を置き換え）
- Modify: `config.yaml.example:10`
- Test: `tests/test_config.py`（作業ツリーの変更をそのまま使う）
- Commit にも含める: `pyproject.toml`、`uv.lock`（作業ツリーの PyYAML 追加）

**Interfaces:**
- Produces: `config.Config(log_level="INFO", log_file=None, timeout=30, max_retries=3, user_agent=...)`。不正な値で `ValueError`。`log_level` は大文字に正規化される
- Produces: `Config.from_file(config_path: str) -> Config`。ファイルがなければ `FileNotFoundError("Config file not found: <path>")`、中身が不正なら `ValueError`
- Produces: `Config.load(config_path: Optional[str] = None, log_level: Optional[str] = None, log_file: Optional[str] = None) -> Config`
- Produces: `Config.to_dict() -> dict[str, Any]`
- `config.YAML_AVAILABLE` は削除される

- [ ] **Step 1: 失敗するテストを確認する**

テストは作業ツリーで書き換え済み。

Run: `PYTHONPATH=src uv run python tests/test_config.py`
Expected: FAIL（`AssertionError: Should have raised FileNotFoundError`）

- [ ] **Step 2: `config.py` を置き換える**

```python
"""Configuration management for enecoQ data fetcher."""

import dataclasses
from typing import Any, Optional

import yaml

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def _require_int(name: str, value: Any, minimum: int) -> None:
    """Check that a config value is an integer of at least minimum.

    Args:
        name: Config key, used in the error message.
        value: Value to check.
        minimum: Smallest accepted value.

    Raises:
        ValueError: If the value is not an integer or is below minimum.
    """
    # bool is a subclass of int, but "true" is never a valid count.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer: %r" % (name, value))
    if value < minimum:
        raise ValueError("%s must be %d or greater: %r" % (name, minimum, value))


@dataclasses.dataclass
class Config:
    """Configuration for enecoQ data fetcher.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Path to log file, or None to log only to the console.
        timeout: Browser operation timeout in seconds.
        max_retries: Number of retries after the first failed attempt.
        user_agent: User agent string for the browser.
    """

    log_level: str = "INFO"
    log_file: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.0 Safari/605.1.15"
    )

    def __post_init__(self) -> None:
        """Validate the values and normalize the log level.

        Raises:
            ValueError: If a value has the wrong type or is out of range.
        """
        if (
            not isinstance(self.log_level, str)
            or self.log_level.upper() not in LOG_LEVELS
        ):
            raise ValueError(
                "log_level must be one of %s: %r"
                % (", ".join(LOG_LEVELS), self.log_level)
            )
        self.log_level = self.log_level.upper()
        if self.log_file is not None and not isinstance(self.log_file, str):
            raise ValueError("log_file must be a string: %r" % (self.log_file,))
        _require_int("timeout", self.timeout, minimum=1)
        _require_int("max_retries", self.max_retries, minimum=0)
        if not isinstance(self.user_agent, str) or not self.user_agent:
            raise ValueError("user_agent must be a non-empty string")

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a YAML file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            Config with the values from the file and defaults for the rest.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid YAML, is not a mapping,
                contains unknown keys, or contains invalid values.
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                "Config file not found: %s" % config_path
            ) from e
        except yaml.YAMLError as e:
            raise ValueError(
                "Invalid YAML in %s: %s" % (config_path, e)
            ) from e

        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError(
                "Config file must contain a mapping: %s" % config_path
            )
        known_keys = {field.name for field in dataclasses.fields(cls)}
        unknown_keys = sorted(str(key) for key in data if key not in known_keys)
        if unknown_keys:
            raise ValueError(
                "Unknown keys in %s: %s"
                % (config_path, ", ".join(unknown_keys))
            )
        return cls(**data)

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
    ) -> "Config":
        """Load configuration and apply command-line overrides.

        Args:
            config_path: Optional path to a configuration file.
            log_level: Optional log level that overrides the file.
            log_file: Optional log file path that overrides the file.

        Returns:
            Config with the overrides applied.

        Raises:
            FileNotFoundError: If config_path is given but does not exist.
            ValueError: If the file or an override is invalid.
        """
        config = cls() if config_path is None else cls.from_file(config_path)
        overrides = {}
        if log_level is not None:
            overrides["log_level"] = log_level
        if log_file is not None:
            overrides["log_file"] = log_file
        # replace() runs __post_init__, so overrides are validated too.
        return dataclasses.replace(config, **overrides)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return dataclasses.asdict(self)
```

- [ ] **Step 3: `config.yaml.example` の説明を直す**

`config.yaml.example` の 10 行目を次に置き換える。

```yaml
max_retries: 3  # Retries after the first failed attempt (0 disables retries)
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `PYTHONPATH=src uv run python tests/test_config.py`
Expected: PASS（最後に `✓ All configuration tests passed!`）

- [ ] **Step 5: コミットする**

```bash
git add src/enecoq_data_fetcher/config.py config.yaml.example tests/test_config.py pyproject.toml uv.lock
git commit -m "fix(config): validate config files and require PyYAML" -m "PyYAML was not a dependency, so config.yaml was silently ignored on installed copies. Values are now type-checked, unknown keys are rejected, a missing explicit file raises FileNotFoundError, and log_file can be overridden like log_level."
```

---

### Task 2: logger の秘密値マスク

**Files:**
- Modify: `src/enecoq_data_fetcher/logger.py`（全体を置き換え）
- Test: `tests/test_logger.py`

**Interfaces:**
- Produces: `logger.setup_logger(log_level: str = "INFO", log_file: Optional[str] = None, secrets: Iterable[str] = ()) -> logging.Logger`
- Produces: `logger.SensitiveDataFilter(secrets: Iterable[str] = ())`
- Produces: `logger.get_logger() -> logging.Logger`（変更なし）
- Produces: `logger.MASK = "****"`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_logger.py` の `test_sensitive_data_filter` を削除し、同じ位置に次を追加する。`if __name__ == "__main__":` ブロックの `test_sensitive_data_filter()` も新しい 5 関数の呼び出しに置き換える。

```python
def test_sensitive_data_filter_masks_secret_in_args():
    """Test that a secret passed as a format argument is masked."""
    filter_obj = logger.SensitiveDataFilter(["s3cr3t"])
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Login with %s failed after %d tries",
        args=("s3cr3t", 3),
        exc_info=None,
    )
    
    assert filter_obj.filter(record) is True
    assert record.getMessage() == "Login with **** failed after 3 tries"
    
    print("✓ test_sensitive_data_filter_masks_secret_in_args passed")


def test_sensitive_data_filter_keeps_other_messages():
    """Test that messages without secrets keep their format arguments."""
    filter_obj = logger.SensitiveDataFilter(["s3cr3t"])
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="password field: %s",
        args=("filled",),
        exc_info=None,
    )
    
    assert filter_obj.filter(record) is True
    assert record.getMessage() == "password field: filled"
    assert record.args == ("filled",)
    
    print("✓ test_sensitive_data_filter_keeps_other_messages passed")


def test_setup_logger_masks_secrets_in_file():
    """Test that setup_logger masks the given secrets in the log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "secret.log")
        log = logger.setup_logger(log_file=log_file, secrets=["s3cr3t"])
        
        log.error("Request failed: %s", "token=s3cr3t")
        for handler in log.handlers:
            handler.flush()
        
        content = Path(log_file).read_text()
        assert "s3cr3t" not in content
        assert "token=****" in content
    
    print("✓ test_setup_logger_masks_secrets_in_file passed")


def test_setup_logger_does_not_duplicate_filters():
    """Test that calling setup_logger twice keeps a single filter."""
    logger.setup_logger(secrets=["one"])
    log = logger.setup_logger(secrets=["two"])
    
    assert len(log.filters) == 1
    assert len(log.handlers) == 1
    
    print("✓ test_setup_logger_does_not_duplicate_filters passed")


def test_console_handler_follows_current_stderr():
    """Test that console logs go to sys.stderr as it is when emitting."""
    log = logger.setup_logger()
    original_stderr = sys.stderr
    replaced = io.StringIO()
    try:
        sys.stderr = replaced
        log.warning("After replacing stderr")
    finally:
        sys.stderr = original_stderr
    
    assert "After replacing stderr" in replaced.getvalue()
    print("✓ test_console_handler_follows_current_stderr passed")
```

`tests/test_logger.py` の import に `import io` と `import sys` を追加する（標準ライブラリの import を辞書順に並べる）。

- [ ] **Step 2: テストが失敗することを確認する**

Run: `PYTHONPATH=src uv run python tests/test_logger.py`
Expected: FAIL（`test_sensitive_data_filter_masks_secret_in_args` で `AssertionError`。今のフィルターは引数を伏せない）

- [ ] **Step 3: `logger.py` を置き換える**

```python
"""Logging configuration for enecoQ data fetcher."""

import logging
import pathlib
import sys
from collections.abc import Iterable
from typing import Optional

LOGGER_NAME = "enecoq_data_fetcher"

# Replacement for secret values in log messages
MASK = "****"


class _StderrHandler(logging.StreamHandler):
    """Writes to sys.stderr as it is at emit time.

    A plain StreamHandler keeps the stream it was created with, so after
    sys.stderr is replaced (as click.testing.CliRunner does) it writes to a
    closed stream.
    """

    def __init__(self) -> None:
        """Initialize the handler."""
        super().__init__(sys.stderr)

    @property
    def stream(self):
        """Return the current sys.stderr."""
        return sys.stderr

    @stream.setter
    def stream(self, value) -> None:
        """Ignore assignments; the stream is always sys.stderr."""


class SensitiveDataFilter(logging.Filter):
    """Replaces known secret values in log messages with a mask."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        """Initialize the filter.

        Args:
            secrets: Values that must never appear in logs, such as the
                enecoQ password. Empty values are ignored.
        """
        super().__init__()
        # Longer secrets first, so one that contains another is fully masked.
        self._secrets = sorted(
            (secret for secret in secrets if secret), key=len, reverse=True
        )

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask secrets in the formatted message of a record.

        Args:
            record: Log record to filter.

        Returns:
            Always True, so the record is still emitted.
        """
        if not self._secrets:
            return True
        message = record.getMessage()
        masked = message
        for secret in self._secrets:
            masked = masked.replace(secret, MASK)
        if masked != message:
            # The secret may be in record.args, so store the masked result
            # as a message that needs no further formatting.
            record.msg = masked
            record.args = None
        return True


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    secrets: Iterable[str] = (),
) -> logging.Logger:
    """Set up the package logger with console and optional file handlers.

    Calling this again replaces the previous handlers and filter.

    Args:
        log_level: Console log level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to a log file that receives DEBUG and above.
        secrets: Values to mask in every log message.

    Returns:
        Configured logger instance.
    """
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(logging.DEBUG)

    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()
    for existing_filter in list(log.filters):
        log.removeFilter(existing_filter)
    log.addFilter(SensitiveDataFilter(secrets))

    # Logs go to stderr so they never mix with JSON on stdout.
    console_handler = _StderrHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    log.addHandler(console_handler)

    if log_file is not None:
        pathlib.Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        log.addHandler(file_handler)

    return log


def get_logger() -> logging.Logger:
    """Get the package logger.

    Returns:
        Logger instance.
    """
    return logging.getLogger(LOGGER_NAME)
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `PYTHONPATH=src uv run python tests/test_logger.py && PYTHONPATH=src uv run python tests/test_logging_integration.py`
Expected: PASS（`All logger tests passed!` と `All integration tests passed!`）

- [ ] **Step 5: コミットする**

```bash
git add src/enecoq_data_fetcher/logger.py tests/test_logger.py
git commit -m "fix(logger): mask actual secret values instead of keywords" -m "The keyword filter missed secrets passed as format arguments and could break formatting by rewriting the format string. It also added a new filter on every setup call. The filter now masks the given secret values in the formatted message and is replaced on each setup. The console handler follows the current sys.stderr, so it no longer writes to a closed stream after a test runner swaps stderr."
```

---

### Task 3: authenticator のエラーの切り分け

**Files:**
- Modify: `src/enecoq_data_fetcher/authenticator.py`（全体を置き換え）
- Test: `tests/test_authenticator.py`（作業ツリーの変更に 1 関数追加）
- Commit にも含める: `src/enecoq_data_fetcher/exceptions.py`（作業ツリーの書式変更）

**Interfaces:**
- Produces: `authenticator.EnecoQAuthenticator(email: str, password: str)`（`user_agent` 引数は削除）
- Produces: `login(page: sync_api.Page) -> None`。ログイン情報が拒否されたとき、またはログインフォームがないときだけ `AuthenticationError`。Playwright のエラー（`sync_api.Error`、`sync_api.TimeoutError`）はそのまま送出
- Produces: `is_logged_in(page: sync_api.Page) -> bool`

- [ ] **Step 1: 失敗するテストを追加する**

`tests/test_authenticator.py` の `test_login_unexpected_error` の後に次を追加し、`if __name__ == "__main__":` ブロックの `test_login_unexpected_error()` の直後に `test_login_timeout_propagates()` を追加する。

```python
def test_login_timeout_propagates():
    """Test that a timeout after submitting propagates for a retry."""
    auth = authenticator.EnecoQAuthenticator(
        email="test@example.com",
        password="test123"
    )
    
    mock_page = Mock()
    mock_email_input = Mock()
    mock_email_input.is_visible.return_value = True
    mock_page.locator.return_value = mock_email_input
    mock_page.wait_for_load_state.side_effect = sync_api.TimeoutError(
        "Timeout 30000ms exceeded"
    )
    
    try:
        auth.login(mock_page)
        assert False, "Should have raised playwright TimeoutError"
    except exceptions.AuthenticationError:
        assert False, "Timeouts must not become AuthenticationError"
    except sync_api.TimeoutError:
        pass
    
    print("✓ Login timeout propagates test passed")
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `PYTHONPATH=src uv run python tests/test_authenticator.py`
Expected: FAIL（`AssertionError: Browser errors must not become AuthenticationError`）

- [ ] **Step 3: `authenticator.py` を置き換える**

```python
"""Authentication component for enecoQ web service."""

from playwright import sync_api

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
                return "Authentication failed: %s" % error_text.strip()
        return "Authentication failed"
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `PYTHONPATH=src uv run python tests/test_authenticator.py`
Expected: PASS（すべての `✓ ... test passed`）

- [ ] **Step 5: コミットする**

```bash
git add src/enecoq_data_fetcher/authenticator.py src/enecoq_data_fetcher/exceptions.py tests/test_authenticator.py
git commit -m "fix(authenticator): let browser errors propagate for retry" -m "Wrapping every exception in AuthenticationError made network errors and timeouts during login look like rejected credentials, so they were never retried. Only a missing login form or a rejected login raises AuthenticationError now. The unused user_agent argument is removed because the browser context sets it."
```

---

### Task 4: fetcher の値抽出と timestamp

**Files:**
- Modify: `src/enecoq_data_fetcher/fetcher.py`（全体を置き換え）
- Test: `tests/test_fetcher.py`

**Interfaces:**
- Consumes: なし
- Produces: `fetcher.EnecoQDataFetcher(page: sync_api.Page)`、属性 `page`
- Produces: `fetch_today_data() -> models.PowerData` / `fetch_month_data() -> models.PowerData`。失敗時は `FetchError`（メッセージは `Failed to fetch today's data: ...` / `Failed to fetch month's data: ...`、コードは `FETCH_TODAY_ERROR` / `FETCH_MONTH_ERROR`）
- Produces: `_extract_value(iframe: sync_api.Frame, alt: str) -> float`。値がない、または数値でなければ `FetchError`
- `PowerData.timestamp` はローカルのオフセット付き（aware）の datetime になる

- [ ] **Step 1: 既存テストを Playwright のエラーに合わせ、新しいテストを追加する**

`tests/test_fetcher.py` の先頭の import に `from playwright import sync_api` を追加する（`from unittest.mock import Mock` の後、空行を挟む）。

`test_select_period_error` の `mock_select.select_option.side_effect = Exception("Selector error")` を次に置き換える。

```python
    mock_select.select_option.side_effect = sync_api.Error("Selector error")
```

`test_fetch_today_data_error` と `test_fetch_month_data_error` の `mock_page.wait_for_selector.side_effect = Exception("Network error")` を、それぞれ次に置き換える。

```python
    mock_page.wait_for_selector.side_effect = sync_api.Error("Network error")
```

`test_get_enecoq_iframe_waits_for_late_rendering` の後に次の 3 関数を追加し、`if __name__ == "__main__":` ブロックの最後の呼び出しの後にも 3 つ追加する。

```python
def test_fetch_month_data_success():
    """Test a full month fetch with separators and a local timestamp."""
    mock_page = Mock()
    mock_iframe = _create_mock_iframe_with_data(
        "1,234.5kWh", "12,345円", "6.53kg"
    )
    mock_page.frames = [mock_iframe]
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    data = data_fetcher.fetch_month_data()
    
    assert data.period == "month"
    assert data.usage.value == 1234.5
    assert data.cost.value == 12345.0
    assert data.co2.value == 6.53
    assert data.timestamp.utcoffset() is not None
    assert "+" in data.to_dict()["timestamp"] or "-" in data.to_dict()["timestamp"][19:]
    print("✓ Fetch month data success test passed")


def test_fetch_month_data_placeholder_value():
    """Test that a placeholder instead of a number fails the fetch."""
    mock_page = Mock()
    mock_iframe = _create_mock_iframe_with_data("--kWh", "0円", "0kg")
    mock_page.frames = [mock_iframe]
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    try:
        data_fetcher.fetch_month_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to fetch month's data" in str(e)
        assert "power usage" in str(e)
    print("✓ Fetch month data placeholder value test passed")


def test_fetch_today_data_missing_value():
    """Test that a missing value fails the fetch instead of returning 0."""
    mock_page = Mock()
    mock_iframe = _create_mock_iframe_with_data("1kWh", "2円", "3kg")
    base_locator = mock_iframe.locator.side_effect
    
    def locator_without_co2(selector):
        if "img[alt='CO2']" in selector:
            return Mock(count=Mock(return_value=0))
        return base_locator(selector)
    
    mock_iframe.locator.side_effect = locator_without_co2
    mock_page.frames = [mock_iframe]
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    try:
        data_fetcher.fetch_today_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert e.error_code == "FETCH_TODAY_ERROR"
        assert "CO2 emission" in str(e)
    print("✓ Fetch today data missing value test passed")
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `PYTHONPATH=src uv run python tests/test_fetcher.py`
Expected: FAIL（`AttributeError: 'EnecoQDataFetcher' object has no attribute '_extract_value'`）

- [ ] **Step 3: `fetcher.py` を置き換える**

```python
"""Data fetcher component for enecoQ web service."""

import datetime
import re

from playwright import sync_api

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger
from enecoq_data_fetcher import models


class EnecoQDataFetcher:
    """Fetches and parses power data from the enecoQ widget.

    Attributes:
        page: Playwright page showing the logged-in CYBERHOME portal.
    """

    # Element the enecoQ widget renders once its data is available
    DATA_MARKER_SELECTOR = "img[alt='使用量']"

    # Time budget for the enecoQ iframe to render its data
    IFRAME_TIMEOUT_MS = 10000
    IFRAME_POLL_INTERVAL_MS = 500

    # Time for the widget to refresh its values after the period changes
    DATA_UPDATE_WAIT_MS = 2000

    # Labels of the period options in the widget's dropdown
    PERIOD_LABELS = {"today": "今日", "month": "今月"}

    # English names for the alt text of each value's image, used in messages
    VALUE_NAMES = {
        "CO2": "CO2 emission",
        "使用料金": "power cost",
        "使用量": "power usage",
    }

    # Values may carry thousands separators, such as "12,345円".
    _NUMBER_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?")

    def __init__(self, page: sync_api.Page) -> None:
        """Initialize fetcher with Playwright page.

        Args:
            page: Playwright page showing the logged-in portal.
        """
        self.page = page
        self._log = logger.get_logger()

    def fetch_today_data(self) -> models.PowerData:
        """Fetch today's power data.

        Returns:
            PowerData object containing today's data.

        Raises:
            FetchError: If the data cannot be retrieved or parsed.
        """
        return self._fetch_data_for_period("today")

    def fetch_month_data(self) -> models.PowerData:
        """Fetch this month's power data.

        Returns:
            PowerData object containing this month's data.

        Raises:
            FetchError: If the data cannot be retrieved or parsed.
        """
        return self._fetch_data_for_period("month")

    def _fetch_data_for_period(self, period: str) -> models.PowerData:
        """Select the period in the widget and read its values.

        Args:
            period: Data period ("today" or "month").

        Returns:
            PowerData object containing the requested data.

        Raises:
            FetchError: If the data cannot be retrieved or parsed.
        """
        self._log.info("Fetching %s data", period)
        try:
            iframe = self._get_enecoq_iframe()
            self._select_period(iframe, period)
            self.page.wait_for_timeout(self.DATA_UPDATE_WAIT_MS)
            power_data = models.PowerData(
                period=period,
                timestamp=datetime.datetime.now().astimezone(),
                usage=models.PowerUsage(
                    value=self._extract_value(iframe, "使用量")
                ),
                cost=models.PowerCost(
                    value=self._extract_value(iframe, "使用料金")
                ),
                co2=models.CO2Emission(
                    value=self._extract_value(iframe, "CO2")
                ),
            )
        except (exceptions.FetchError, sync_api.Error) as e:
            self._log.error("Failed to fetch %s's data: %s", period, e)
            raise exceptions.FetchError(
                "Failed to fetch %s's data: %s" % (period, e),
                "FETCH_%s_ERROR" % period.upper(),
            ) from e
        self._log.info("Successfully fetched %s data", period)
        return power_data

    def _get_enecoq_iframe(self) -> sync_api.Frame:
        """Get the iframe containing the enecoQ widget.

        The widget is identified by the data marker it renders. Other iframes
        on the page hold unrelated select elements, so they are never used as
        a substitute.

        Returns:
            Frame object for the enecoQ widget.

        Raises:
            FetchError: If the widget does not render in time.
        """
        try:
            self.page.wait_for_selector("iframe", timeout=self.IFRAME_TIMEOUT_MS)

            # The widget may still be rendering, so poll for the data marker.
            waited_ms = 0
            while True:
                for frame in self.page.frames:
                    if frame.locator(self.DATA_MARKER_SELECTOR).count() > 0:
                        self._log.debug("Found enecoQ iframe: %s", frame.url)
                        return frame
                if waited_ms >= self.IFRAME_TIMEOUT_MS:
                    break
                self.page.wait_for_timeout(self.IFRAME_POLL_INTERVAL_MS)
                waited_ms += self.IFRAME_POLL_INTERVAL_MS
        except sync_api.Error as e:
            raise exceptions.FetchError(
                "Failed to locate iframe: %s" % e, "IFRAME_ERROR"
            ) from e

        # The widget is unavailable for a while after the month rollover.
        # Fail fast so the caller gets an accurate reason instead of a period
        # selection timeout on an unrelated iframe.
        raise exceptions.FetchError(
            "enecoQ iframe not found: no iframe rendered %s within %sms"
            % (self.DATA_MARKER_SELECTOR, self.IFRAME_TIMEOUT_MS),
            "IFRAME_NOT_FOUND",
        )

    def _select_period(self, iframe: sync_api.Frame, period: str) -> None:
        """Select the period in the widget's dropdown.

        Args:
            iframe: Frame containing the widget.
            period: Data period ("today" or "month").

        Raises:
            FetchError: If the period is invalid or cannot be selected.
        """
        label = self.PERIOD_LABELS.get(period)
        if label is None:
            raise exceptions.FetchError(
                "Invalid period: %s" % period, "INVALID_PERIOD"
            )
        self._log.debug("Selecting period: %s", period)
        try:
            iframe.locator("select").first.select_option(label=label)
        except sync_api.Error as e:
            raise exceptions.FetchError(
                "Failed to select period: %s" % e, "PERIOD_SELECT_ERROR"
            ) from e

    def _extract_value(self, iframe: sync_api.Frame, alt: str) -> float:
        """Read the number shown next to the widget image with the alt text.

        Args:
            iframe: Frame containing the widget.
            alt: Alt text of the image that labels the value, such as "使用量".

        Returns:
            The value without its unit.

        Raises:
            FetchError: If the value is missing or is not a number.
        """
        name = self.VALUE_NAMES.get(alt, alt)
        dt_locator = iframe.locator("dt:has(img[alt='%s'])" % alt)
        dd_locator = dt_locator.locator("xpath=following-sibling::dd[1]")
        if dt_locator.count() == 0 or dd_locator.count() == 0:
            raise exceptions.FetchError(
                "Value for %s not found" % name, "VALUE_NOT_FOUND"
            )

        text = dd_locator.first.text_content() or ""
        match = self._NUMBER_PATTERN.search(text)
        if match is None:
            raise exceptions.FetchError(
                "Could not parse %s from %r" % (name, text),
                "VALUE_PARSE_ERROR",
            )
        value = float(match.group(0).replace(",", ""))
        self._log.debug("Extracted %s: %s", name, value)
        return value
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `PYTHONPATH=src uv run python tests/test_fetcher.py`
Expected: PASS（最後に `✓ All fetcher tests passed!`）

- [ ] **Step 5: コミットする**

```bash
git add src/enecoq_data_fetcher/fetcher.py tests/test_fetcher.py
git commit -m "fix(fetcher): fail on missing values and parse thousands separators" -m "Missing values were reported as 0.0, which Home Assistant records as a meter reset, and the number pattern read 1,234 as 1. The three extractors are merged into _extract_value, which raises FetchError instead. Errors are wrapped and logged once per fetch, and the timestamp now carries the local UTC offset."
```

---

### Task 5: controller のリトライとブラウザ設定

**Files:**
- Modify: `src/enecoq_data_fetcher/controller.py`（全体を置き換え）
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `authenticator.EnecoQAuthenticator(email, password)`（Task 3）、`fetcher.EnecoQDataFetcher(page)` の `fetch_today_data()` / `fetch_month_data()`（Task 4）、`config.Config`（Task 1）
- Produces: `controller.EnecoQController(email: str, password: str, config: Optional[config.Config] = None, max_retries: Optional[int] = None, backoff_factor: int = 2)`。属性 `_config`、`_max_retries`
- Produces: `fetch_power_data(period: str, output_format: str = "json", output_path: Optional[str] = None) -> models.PowerData`
- 試行回数は `_max_retries + 1`。`FetchError` と `sync_api.Error` はリトライ、`AuthenticationError` はリトライしない。使い切ると `FetchError`（コード `RETRY_EXHAUSTED`）

- [ ] **Step 1: 失敗するテストを追加する**

`tests/test_integration.py` の import に `from playwright import sync_api` を追加する（`from unittest.mock import Mock, patch` の後、空行を挟む）。

`test_error_handling_fetch` の `runner.invoke(...)` を `with patch("time.sleep"):` の中に入れる（毎回失敗するのでリトライの待ち時間が実際に発生するのを避ける）。

```python
                # Run CLI
                runner = CliRunner()
                with patch("time.sleep"):  # Skip actual sleep
                    result = runner.invoke(cli.main, [
                        "--email", "test@example.com",
                        "--password", "test123",
                        "--format", "console"
                    ])
```

`test_data_model_serialization` の前に次のヘルパーと 5 関数を追加し、`if __name__ == "__main__":` ブロックの `test_retry_mechanism()` の後にも 5 つ追加する。

```python
def _mock_browser(mock_playwright):
    """Wire a mocked sync_playwright to return a mock browser.

    Args:
        mock_playwright: Patched sync_playwright.

    Returns:
        Tuple of the mock browser, context, and page.
    """
    mock_browser = Mock()
    mock_context = Mock()
    mock_page = Mock()
    launcher = mock_playwright.return_value.__enter__.return_value.chromium
    launcher.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    return mock_browser, mock_context, mock_page


def _sample_month_data():
    """Return PowerData for a successful month fetch."""
    return models.PowerData(
        period="month",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=450.0),
        cost=models.PowerCost(value=12500.0),
        co2=models.CO2Emission(value=225.0),
    )


def test_retry_on_login_timeout():
    """Test that a browser timeout during login is retried."""
    print("\n=== Testing retry on login timeout ===")
    
    with patch("enecoq_data_fetcher.controller.sync_api.sync_playwright") as mock_playwright:
        mock_browser, _, _ = _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login") as mock_login:
            mock_login.side_effect = [
                sync_api.TimeoutError("Timeout 30000ms exceeded"),
                None,
            ]
            with patch("enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data") as mock_fetch:
                mock_fetch.return_value = _sample_month_data()
                ctl = controller.EnecoQController(
                    "test@example.com", "test123", config=config.Config()
                )
                with patch("time.sleep"):
                    result = ctl.fetch_power_data("month", "console")
    
    assert result.usage.value == 450.0
    assert mock_login.call_count == 2
    assert mock_browser.close.call_count == 2
    print("✓ Retry on login timeout test passed")


def test_no_retry_on_authentication_error():
    """Test that rejected credentials are not retried."""
    print("\n=== Testing no retry on authentication error ===")
    
    with patch("enecoq_data_fetcher.controller.sync_api.sync_playwright") as mock_playwright:
        mock_browser, _, _ = _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login") as mock_login:
            mock_login.side_effect = exceptions.AuthenticationError("Rejected")
            ctl = controller.EnecoQController(
                "test@example.com", "wrong", config=config.Config()
            )
            try:
                with patch("time.sleep") as mock_sleep:
                    ctl.fetch_power_data("month", "console")
                assert False, "Should have raised AuthenticationError"
            except exceptions.AuthenticationError:
                pass
    
    assert mock_login.call_count == 1
    assert not mock_sleep.called
    assert mock_browser.close.call_count == 1
    print("✓ No retry on authentication error test passed")


def test_retries_are_added_to_first_attempt():
    """Test that max_retries counts retries after the first attempt."""
    print("\n=== Testing retry count ===")
    
    with patch("enecoq_data_fetcher.controller.sync_api.sync_playwright") as mock_playwright:
        _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch("enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data") as mock_fetch:
                mock_fetch.side_effect = exceptions.FetchError("Widget down")
                ctl = controller.EnecoQController(
                    "test@example.com", "test123",
                    config=config.Config(max_retries=2),
                )
                try:
                    with patch("time.sleep") as mock_sleep:
                        ctl.fetch_power_data("month", "console")
                    assert False, "Should have raised FetchError"
                except exceptions.FetchError as e:
                    assert e.error_code == "RETRY_EXHAUSTED"
    
    assert mock_fetch.call_count == 3
    assert [c.args[0] for c in mock_sleep.call_args_list] == [2, 4]
    print("✓ Retry count test passed")


def test_zero_retries_tries_once():
    """Test that max_retries of 0 still makes one attempt."""
    print("\n=== Testing zero retries ===")
    
    with patch("enecoq_data_fetcher.controller.sync_api.sync_playwright") as mock_playwright:
        _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch("enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data") as mock_fetch:
                mock_fetch.return_value = _sample_month_data()
                ctl = controller.EnecoQController(
                    "test@example.com", "test123",
                    config=config.Config(max_retries=0),
                )
                result = ctl.fetch_power_data("month", "console")
    
    assert result.cost.value == 12500.0
    assert mock_fetch.call_count == 1
    print("✓ Zero retries test passed")


def test_browser_context_uses_config():
    """Test that user_agent and timeout from the config reach the browser."""
    print("\n=== Testing browser context settings ===")
    
    with patch("enecoq_data_fetcher.controller.sync_api.sync_playwright") as mock_playwright:
        mock_browser, mock_context, _ = _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch("enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data") as mock_fetch:
                mock_fetch.return_value = _sample_month_data()
                ctl = controller.EnecoQController(
                    "test@example.com", "test123",
                    config=config.Config(user_agent="TestAgent/1.0", timeout=45),
                )
                ctl.fetch_power_data("month", "console")
    
    mock_browser.new_context.assert_called_once_with(user_agent="TestAgent/1.0")
    mock_context.set_default_timeout.assert_called_once_with(45000)
    print("✓ Browser context settings test passed")
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `PYTHONPATH=src uv run python tests/test_integration.py`
Expected: FAIL（`AttributeError: module 'enecoq_data_fetcher.controller' has no attribute 'sync_api'`）

- [ ] **Step 3: `controller.py` を置き換える**

```python
"""Main controller for enecoQ data fetcher."""

import time
from collections.abc import Callable
from typing import Optional, TypeVar

from playwright import sync_api

from enecoq_data_fetcher import authenticator
from enecoq_data_fetcher import config as config_module
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import exporter
from enecoq_data_fetcher import fetcher
from enecoq_data_fetcher import logger
from enecoq_data_fetcher import models

_T = TypeVar("_T")


class EnecoQController:
    """Runs a fetch: browser lifecycle, login, data retrieval, and export.

    Transient failures are retried by starting over with a new browser.
    """

    DEFAULT_BACKOFF_FACTOR = 2

    def __init__(
        self,
        email: str,
        password: str,
        config: Optional[config_module.Config] = None,
        max_retries: Optional[int] = None,
        backoff_factor: int = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """Initialize controller with credentials.

        Args:
            email: User's email for enecoQ authentication.
            password: User's password for enecoQ authentication.
            config: Optional configuration. Defaults to Config().
            max_retries: Optional number of retries after the first attempt.
                Overrides config.max_retries.
            backoff_factor: Base of the exponential wait between attempts,
                in seconds.

        Raises:
            ValueError: If max_retries is negative.
        """
        self._config = config or config_module.Config()
        self._max_retries = (
            self._config.max_retries if max_retries is None else max_retries
        )
        if self._max_retries < 0:
            raise ValueError(
                "max_retries must be 0 or greater: %s" % self._max_retries
            )
        self._backoff_factor = backoff_factor
        self._authenticator = authenticator.EnecoQAuthenticator(email, password)
        self._log = logger.get_logger()

    def fetch_power_data(
        self,
        period: str,
        output_format: str = "json",
        output_path: Optional[str] = None,
    ) -> models.PowerData:
        """Fetch power data for the period and export it.

        Args:
            period: Data period ("today" or "month").
            output_format: Output format ("json" or "console").
            output_path: Optional file path for JSON output.

        Returns:
            PowerData object containing the fetched data.

        Raises:
            AuthenticationError: If the credentials are rejected.
            FetchError: If fetching fails on every attempt.
            ExportError: If exporting fails.
        """
        if period not in ("today", "month"):
            raise exceptions.FetchError(
                "Invalid period: %s. Must be 'today' or 'month'." % period,
                "INVALID_PERIOD",
            )

        self._log.info("Starting data fetch for period: %s", period)
        power_data = self._execute_with_retry(lambda: self._fetch_once(period))
        self._log.info("Data fetch completed successfully")

        self._export_data(power_data, output_format, output_path)
        return power_data

    def _fetch_once(self, period: str) -> models.PowerData:
        """Launch a browser, log in, and fetch the data once.

        Args:
            period: Data period ("today" or "month").

        Returns:
            PowerData object containing the fetched data.

        Raises:
            AuthenticationError: If the credentials are rejected.
            FetchError: If the data cannot be retrieved or parsed.
            playwright.sync_api.Error: If the browser fails.
        """
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=self._config.user_agent
                )
                context.set_default_timeout(self._config.timeout * 1000)
                page = context.new_page()

                self._authenticator.login(page)

                data_fetcher = fetcher.EnecoQDataFetcher(page)
                if period == "today":
                    return data_fetcher.fetch_today_data()
                return data_fetcher.fetch_month_data()
            finally:
                # Closing the browser also closes its contexts and pages.
                browser.close()

    def _execute_with_retry(self, operation: Callable[[], _T]) -> _T:
        """Run the operation, retrying transient failures with backoff.

        FetchError and browser errors are retried. Everything else,
        including AuthenticationError, propagates immediately.

        Args:
            operation: Callable to run.

        Returns:
            Result of the operation.

        Raises:
            FetchError: If every attempt fails with a transient error.
        """
        attempts = self._max_retries + 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return operation()
            except (exceptions.FetchError, sync_api.Error) as e:
                last_error = e
                self._log.warning(
                    "Attempt %s/%s failed: %s", attempt, attempts, e
                )
            if attempt < attempts:
                wait_time = self._backoff_factor ** attempt
                self._log.info("Retrying in %s seconds", wait_time)
                time.sleep(wait_time)

        raise exceptions.FetchError(
            "Operation failed after %s attempts: %s" % (attempts, last_error),
            "RETRY_EXHAUSTED",
        ) from last_error

    def _export_data(
        self,
        power_data: models.PowerData,
        output_format: str,
        output_path: Optional[str],
    ) -> None:
        """Export power data in the given format.

        Args:
            power_data: PowerData object to export.
            output_format: Output format ("json" or "console").
            output_path: Optional file path for JSON output.

        Raises:
            ExportError: If the format is invalid or exporting fails.
        """
        self._log.info("Exporting data in %s format", output_format)
        data_exporter = exporter.DataExporter()
        if output_format == "json":
            data_exporter.export_json(power_data, output_path)
        elif output_format == "console":
            data_exporter.export_console(power_data)
        else:
            raise exceptions.ExportError(
                "Invalid output format: %s" % output_format,
                "INVALID_FORMAT",
            )
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `PYTHONPATH=src uv run python tests/test_integration.py`
Expected: PASS（最後に `✓ All integration tests passed!`。`test_retry_mechanism` の `mock_fetch.call_count == 2` もこのまま通る）

- [ ] **Step 5: コミットする**

```bash
git add src/enecoq_data_fetcher/controller.py tests/test_integration.py
git commit -m "fix(controller): retry browser errors and apply the user agent" -m "Retries now cover FetchError and Playwright errors from the whole browser session, and max_retries counts retries after the first attempt. The user_agent setting was never applied; the browser context now uses it. The unreachable _authenticate_with_retry, the unused constants, and the nested try/finally blocks are removed."
```

---

### Task 6: cli の設定ファイルとエラー表示

**Files:**
- Modify: `src/enecoq_data_fetcher/cli.py`（全体を置き換え）
- Modify: `src/enecoq_data_fetcher/exporter.py:67`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `config.Config.load(config_path, log_level, log_file)`（Task 1）、`logger.setup_logger(log_level, log_file, secrets)`（Task 2）、`controller.EnecoQController(email, password, config=...)` と `fetch_power_data(period=..., output_format=..., output_path=...)`（Task 5）
- Produces: `cli.main`（Click コマンド）。`--config` のデフォルトは `None`、未指定時はカレントディレクトリの `config.yaml` を自動で読む

- [ ] **Step 1: 失敗するテストを追加する**

`tests/test_cli.py` の import に `import os` を追加する（先頭の `from unittest.mock import Mock, patch` の前）。`test_cli_missing_explicit_config` の後に次を追加し、`if __name__ == "__main__":` ブロックの最後の呼び出しの後にも 5 つ追加する。

```python
def _sample_today_data():
    """Return PowerData for a successful today fetch."""
    return models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )


def test_cli_invalid_config_content():
    """Test that an invalid config file exits with the argument error code."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("bad.yaml", "w", encoding="utf-8") as f:
            f.write("timeout: thirty\n")
        result = runner.invoke(cli.main, [
            "--email", "test@example.com",
            "--password", "test123",
            "--config", "bad.yaml",
        ])
    
    assert result.exit_code == 6, result.output
    assert "timeout" in result.output
    print("✓ CLI rejects invalid config content")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_loads_default_config_when_present(mock_controller_class):
    """Test that config.yaml in the working directory is loaded by default."""
    mock_controller_class.return_value.fetch_power_data.return_value = (
        _sample_today_data()
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("config.yaml", "w", encoding="utf-8") as f:
            f.write("timeout: 90\n")
        result = runner.invoke(cli.main, [
            "--email", "test@example.com",
            "--password", "test123",
            "--format", "console",
        ])
    
    assert result.exit_code == 0, result.output
    assert mock_controller_class.call_args.kwargs["config"].timeout == 90
    print("✓ CLI loads config.yaml by default")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_uses_defaults_without_config(mock_controller_class):
    """Test that a missing default config.yaml is not an error."""
    mock_controller_class.return_value.fetch_power_data.return_value = (
        _sample_today_data()
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli.main, [
            "--email", "test@example.com",
            "--password", "test123",
            "--format", "console",
        ])
    
    assert result.exit_code == 0, result.output
    assert mock_controller_class.call_args.kwargs["config"].timeout == 30
    print("✓ CLI uses defaults without config.yaml")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_masks_password_in_log_file(mock_controller_class):
    """Test that the password never reaches the log file."""
    mock_controller_class.return_value.fetch_power_data.side_effect = (
        exceptions.FetchError("Page echoed hunter2-secret back")
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli.main, [
            "--email", "test@example.com",
            "--password", "hunter2-secret",
            "--log-file", "run.log",
        ])
        with open("run.log", encoding="utf-8") as f:
            content = f.read()
    
    assert result.exit_code == 2, result.output
    assert "hunter2-secret" not in content
    assert "Page echoed **** back" in content
    print("✓ CLI masks password in log file")


def test_cli_reports_argument_error_once():
    """Test that an error before logging is set up is shown once."""
    runner = CliRunner()
    result = runner.invoke(cli.main, [
        "--email", "invalid-email",
        "--password", "test123",
    ])
    
    assert result.exit_code == 6
    assert result.output.count("Invalid argument") == 1, result.output
    print("✓ CLI reports argument error once")
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `PYTHONPATH=src uv run python tests/test_cli.py`
Expected: FAIL（`test_cli_missing_explicit_config` の `assert result.exit_code == 6`。今は存在しない `--config` を無視して進む）

- [ ] **Step 3: `cli.py` を置き換える**

```python
"""Command-line interface for enecoQ data fetcher."""

import datetime
import logging
import os
import sys
from typing import NoReturn, Optional

import click

from enecoq_data_fetcher import __version__
from enecoq_data_fetcher import config as config_module
from enecoq_data_fetcher import controller
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger

# Loaded when --config is not given and the file exists
DEFAULT_CONFIG_PATH = "config.yaml"

EXIT_AUTH_ERROR = 1
EXIT_FETCH_ERROR = 2
EXIT_EXPORT_ERROR = 3
EXIT_ENECOQ_ERROR = 4
EXIT_UNEXPECTED_ERROR = 5
EXIT_INVALID_ARGUMENT = 6


@click.command()
@click.version_option(version=__version__, prog_name="enecoq-data-fetcher")
@click.option(
    "--email",
    required=True,
    help="Email address for enecoQ authentication.",
)
@click.option(
    "--password",
    required=True,
    help="Password for enecoQ authentication.",
)
@click.option(
    "--period",
    type=click.Choice(["today", "month"], case_sensitive=False),
    default="month",
    help="Data period to fetch (default: month).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "console"], case_sensitive=False),
    default="json",
    help="Output format (default: json).",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(),
    default=None,
    help="Output file path for JSON format (optional).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="Configuration file path (default: config.yaml if it exists).",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default=None,
    help="Logging level (default: INFO, or from config file).",
)
@click.option(
    "--log-file",
    type=click.Path(),
    default=None,
    help="Log file path (optional, no file logging by default).",
)
def main(
    email: str,
    password: str,
    period: str,
    output_format: str,
    output_path: Optional[str],
    config_path: Optional[str],
    log_level: Optional[str],
    log_file: Optional[str],
) -> None:
    """enecoQ Data Fetcher - Fetch power usage data from enecoQ Web Service.

    This tool retrieves power usage, cost, and CO2 emission data from the
    enecoQ Web Service.

    Examples:

        \b
        # Fetch this month's data and display in console
        $ enecoq-data-fetcher --email user@example.com --password secret --format console

        \b
        # Fetch today's data and save to JSON file
        $ enecoq-data-fetcher --email user@example.com --password secret --period today --output data.json

        \b
        # Fetch with debug logging
        $ enecoq-data-fetcher --email user@example.com --password secret --log-level DEBUG

        \b
        # Use custom config file
        $ enecoq-data-fetcher --email user@example.com --password secret --config /path/to/config.yaml
    """
    log = None
    try:
        _validate_arguments(email, password, output_format, output_path)
        config = _load_config(config_path, log_level, log_file)
        log = logger.setup_logger(
            log_level=config.log_level,
            log_file=config.log_file,
            secrets=[password],
        )
        log.info(
            "Starting enecoQ data fetcher at %s",
            datetime.datetime.now().isoformat(),
        )
        log.debug(
            "Parameters - Period: %s, Format: %s, Config: %s",
            period, output_format, config_path,
        )
        log.debug(
            "Configuration - Log level: %s, Timeout: %s, Max retries: %s",
            config.log_level, config.timeout, config.max_retries,
        )

        enecoq_controller = controller.EnecoQController(
            email, password, config=config
        )
        enecoq_controller.fetch_power_data(
            period=period.lower(),
            output_format=output_format.lower(),
            output_path=output_path,
        )

        if output_path:
            click.echo("Data successfully exported to: %s" % output_path)
            log.info("Data successfully exported to: %s", output_path)
        log.info(
            "enecoQ data fetcher completed at %s",
            datetime.datetime.now().isoformat(),
        )

    except click.BadParameter as e:
        _fail(log, "Invalid argument: %s" % e.message, EXIT_INVALID_ARGUMENT)
    except exceptions.AuthenticationError as e:
        _fail(log, "Authentication error: %s" % e, EXIT_AUTH_ERROR)
    except exceptions.FetchError as e:
        _fail(log, "Fetch error: %s" % e, EXIT_FETCH_ERROR)
    except exceptions.ExportError as e:
        _fail(log, "Export error: %s" % e, EXIT_EXPORT_ERROR)
    except exceptions.EnecoQError as e:
        _fail(log, "Error: %s" % e, EXIT_ENECOQ_ERROR)
    except Exception as e:  # pylint: disable=broad-except
        # Last resort, so users get an exit code instead of a traceback.
        _fail(
            log, "Unexpected error: %s" % e, EXIT_UNEXPECTED_ERROR,
            exc_info=True,
        )


def _load_config(
    config_path: Optional[str],
    log_level: Optional[str],
    log_file: Optional[str],
) -> config_module.Config:
    """Load the configuration for this run.

    Args:
        config_path: Path given with --config, or None to use config.yaml
            in the working directory when it exists.
        log_level: Log level given with --log-level, if any.
        log_file: Log file given with --log-file, if any.

    Returns:
        Loaded configuration.

    Raises:
        click.BadParameter: If the file is missing or invalid.
    """
    if config_path is None and os.path.exists(DEFAULT_CONFIG_PATH):
        config_path = DEFAULT_CONFIG_PATH
    try:
        return config_module.Config.load(
            config_path=config_path, log_level=log_level, log_file=log_file
        )
    except (FileNotFoundError, ValueError) as e:
        raise click.BadParameter(str(e)) from e


def _validate_arguments(
    email: str,
    password: str,
    output_format: str,
    output_path: Optional[str],
) -> None:
    """Validate arguments that Click's option types do not cover.

    Args:
        email: Email address for authentication.
        password: Password for authentication.
        output_format: Output format ("json" or "console").
        output_path: Optional output file path.

    Raises:
        click.BadParameter: If validation fails.
    """
    if "@" not in email:
        raise click.BadParameter("Invalid email address format.")
    if not password:
        raise click.BadParameter("Password cannot be empty.")
    if output_path and output_format.lower() != "json":
        raise click.BadParameter(
            "Output path can only be specified with JSON format."
        )


def _fail(
    log: Optional[logging.Logger],
    message: str,
    exit_code: int,
    exc_info: bool = False,
) -> NoReturn:
    """Report an error and exit.

    Before logging is set up the logger has no handlers, and Python's
    last-resort handler would print the message a second time, so the
    message is only logged once a logger exists.

    Args:
        log: Configured logger, or None if logging is not set up yet.
        message: Error message for the user.
        exit_code: Process exit code.
        exc_info: Whether to log the traceback.
    """
    if log is not None:
        log.error("%s", message, exc_info=exc_info)
    click.echo(message, err=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: exporter の例外をまとめる**

`src/enecoq_data_fetcher/exporter.py` の 67 行目 `except (OSError, IOError) as e:` を次に置き換える（`IOError` は `OSError` の別名）。

```python
        except OSError as e:
```

- [ ] **Step 5: テストが通ることを確認する**

Run: `PYTHONPATH=src uv run python tests/test_cli.py && PYTHONPATH=src uv run python tests/test_exporter.py && PYTHONPATH=src uv run python tests/test_integration.py`
Expected: PASS（`All CLI tests passed!`、exporter の全テスト、`✓ All integration tests passed!`）

- [ ] **Step 6: コミットする**

```bash
git add src/enecoq_data_fetcher/cli.py src/enecoq_data_fetcher/exporter.py tests/test_cli.py
git commit -m "fix(cli): report config errors and mask the password in logs" -m "A missing or invalid --config file was silently ignored; it now exits with code 6, and config.yaml in the working directory is still loaded when --config is omitted. The password is registered with the log filter, errors raised before logging is set up are printed once, and validation that duplicated Click's Choice types is removed."
```

---

### Task 7: テストランナーの合否判定

**Files:**
- Modify: `tests/run_tests.sh`（全体を置き換え）

**Interfaces:**
- Produces: `run_suite <name> <file>` 関数。Task 8 はこれで新しいテストを登録する
- 1 つでも失敗したら終了コード 1、すべて成功なら 0

- [ ] **Step 1: 失敗を見逃すことを確認する**

`grep` を通したパイプラインの終了ステータスは `grep` のものになるので、Python が失敗しても成功扱いになる。

Run: `command cp tests/test_fetcher.py /tmp/test_fetcher.py.bak && printf '\nraise SystemExit(1)\n' >> tests/test_fetcher.py; ./tests/run_tests.sh 2>&1 | grep -E "Fetcher tests|All test suites"; command cp /tmp/test_fetcher.py.bak tests/test_fetcher.py`
Expected: `✓ Fetcher tests passed`（本来は失敗であるべき）

- [ ] **Step 2: `tests/run_tests.sh` を置き換える**

```bash
#!/bin/bash
# Runs every test file and reports which suites failed.
#
# Each test file runs its own tests from its __main__ block, so a suite
# passes exactly when its python process exits with status 0.

set -uo pipefail

cd "$(dirname "$0")/.."
# shellcheck source=/dev/null
source .venv/bin/activate
export PYTHONPATH=src

failed_suites=()

run_suite() {
  local name="$1"
  local file="$2"
  echo "Running $name tests..."
  echo "----------------------------------------"
  if python3 "$file"; then
    echo "✓ $name tests passed"
  else
    echo "✗ $name tests failed"
    failed_suites+=("$name")
  fi
  echo ""
}

echo "========================================"
echo "enecoQ Data Fetcher - Test Suite"
echo "========================================"
echo ""

echo "=== Unit Tests ==="
echo ""
run_suite "Models" tests/test_models.py
run_suite "Exceptions" tests/test_exceptions.py
run_suite "Authenticator" tests/test_authenticator.py
run_suite "Fetcher" tests/test_fetcher.py
run_suite "Config" tests/test_config.py
run_suite "Exporter" tests/test_exporter.py
run_suite "Logger" tests/test_logger.py
run_suite "CLI" tests/test_cli.py

echo "=== Property-Based Tests ==="
echo ""
if python3 -c "import hypothesis" 2>/dev/null; then
  run_suite "Property-based" tests/test_pbt.py
else
  echo "⊘ Skipping property-based tests (hypothesis not installed)"
  echo "  Install with: uv sync --extra test"
  echo ""
fi

echo "=== Integration Tests ==="
echo ""
run_suite "Logging integration" tests/test_logging_integration.py
run_suite "Integration" tests/test_integration.py

echo "========================================"
if [[ ${#failed_suites[@]} -eq 0 ]]; then
  echo "✓ All test suites passed!"
  echo "========================================"
  exit 0
fi
echo "✗ Failed suites: ${failed_suites[*]}"
echo "========================================"
exit 1
```

- [ ] **Step 3: 失敗が検出されることを確認する**

Run: `command cp tests/test_fetcher.py /tmp/test_fetcher.py.bak && printf '\nraise SystemExit(1)\n' >> tests/test_fetcher.py; ./tests/run_tests.sh > /tmp/run_tests.log 2>&1; echo "exit=$?"; grep -E "Fetcher tests|Failed suites" /tmp/run_tests.log; command cp /tmp/test_fetcher.py.bak tests/test_fetcher.py`
Expected: `exit=1`、`✗ Fetcher tests failed`、`✗ Failed suites: Fetcher`

- [ ] **Step 4: 通常の実行で全体が通り、ログのエラーが出ないことを確認する**

Run: `./tests/run_tests.sh > /tmp/run_tests.log 2>&1; echo "exit=$?"; grep -c -E "Logging error|I/O operation on closed file" /tmp/run_tests.log`
Expected: `exit=0` と `0`（Task 2 のハンドラー修正により、以前 `grep` で隠していたログのエラーが出ない）

- [ ] **Step 5: コミットする**

```bash
git add tests/run_tests.sh
git commit -m "test: make run_tests.sh fail when a suite fails" -m "Three suites were piped through grep to hide noise, so their status came from grep and failures were reported as passes. The noise came from a logger handler holding a closed stderr, which the logger now avoids, so the pipes are removed and each suite is judged by its own exit status."
```

---

### Task 8: リリーススクリプトの事前確認

**Files:**
- Modify: `scripts/bump_version.sh`（全体を置き換え）
- Modify: `Makefile`
- Create: `tests/test_bump_version.py`
- Modify: `tests/run_tests.sh`（Task 7 の `run_suite` で登録）

**Interfaces:**
- Produces: `scripts/bump_version.sh {major|minor|patch} [--push]`。成功時は `chore: bump version to X.Y.Z` のコミットとタグ `vX.Y.Z` を作り、`--push` 時は `git push --atomic origin main refs/tags/vX.Y.Z`。事前確認に失敗したら終了コード 1 で何も変更しない

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_bump_version.py` を作る。

```python
"""Tests for scripts/bump_version.sh."""

import os
import pathlib
import shutil
import subprocess
import tempfile

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "bump_version.sh"
VERSION_FILE = pathlib.Path("src") / "enecoq_data_fetcher" / "__init__.py"

# Isolate git from the user's global config, such as commit signing.
GIT_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_NOSYSTEM="1",
    GIT_AUTHOR_NAME="Test",
    GIT_AUTHOR_EMAIL="test@example.com",
    GIT_COMMITTER_NAME="Test",
    GIT_COMMITTER_EMAIL="test@example.com",
)


def _git(repo, *args):
    """Run git in repo and return its stdout."""
    return subprocess.run(
        ["git", *args], cwd=repo, env=GIT_ENV, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _make_repo(tmpdir):
    """Create a work repository at version 1.2.3 pushed to a bare origin.

    Args:
        tmpdir: Directory to create the repositories in.

    Returns:
        Path to the work repository.
    """
    origin = pathlib.Path(tmpdir) / "origin.git"
    work = pathlib.Path(tmpdir) / "work"
    subprocess.run(
        ["git", "init", "--quiet", "--bare", "-b", "main", str(origin)],
        env=GIT_ENV, check=True,
    )
    subprocess.run(
        ["git", "init", "--quiet", "-b", "main", str(work)],
        env=GIT_ENV, check=True,
    )
    (work / "scripts").mkdir()
    shutil.copy(SCRIPT, work / "scripts" / "bump_version.sh")
    (work / VERSION_FILE).parent.mkdir(parents=True)
    (work / VERSION_FILE).write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "--quiet", "-m", "initial")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "--quiet", "-u", "origin", "main")
    return work


def _bump(work, *args):
    """Run the copied script in the work repository."""
    return subprocess.run(
        ["bash", "scripts/bump_version.sh", *args], cwd=work, env=GIT_ENV,
        capture_output=True, text=True,
    )


def _version(work):
    """Return the version line of the work repository."""
    return (work / VERSION_FILE).read_text(encoding="utf-8").strip()


def test_bump_patch_commits_and_tags():
    """Test that a patch bump commits only the version file and tags it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        
        result = _bump(work, "patch")
        
        assert result.returncode == 0, result.stderr
        assert _version(work) == '__version__ = "1.2.4"'
        assert _git(work, "log", "-1", "--format=%s") == "chore: bump version to 1.2.4"
        assert _git(work, "show", "--name-only", "--format=", "HEAD") == str(VERSION_FILE)
        assert _git(work, "tag", "--list") == "v1.2.4"
        assert _git(work, "ls-remote", "--tags", "origin") == ""
    print("✓ Bump patch commits and tags test passed")


def test_bump_minor_and_major_reset_lower_parts():
    """Test that minor and major bumps reset the lower version parts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        assert _bump(work, "minor").returncode == 0
        assert _version(work) == '__version__ = "1.3.0"'
        _git(work, "push", "--quiet", "origin", "main")
        assert _bump(work, "major").returncode == 0
        assert _version(work) == '__version__ = "2.0.0"'
    print("✓ Bump minor and major test passed")


def test_bump_with_push_sends_branch_and_tag():
    """Test that --push sends main and only the new tag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "tag", "local-only")
        
        result = _bump(work, "patch", "--push")
        
        assert result.returncode == 0, result.stderr
        remote_tags = _git(work, "ls-remote", "--tags", "origin")
        assert "refs/tags/v1.2.4" in remote_tags
        assert "local-only" not in remote_tags
        assert _git(work, "rev-parse", "origin/main") == _git(work, "rev-parse", "HEAD")
    print("✓ Bump with push test passed")


def _assert_refused(work, result, head_before):
    """Assert that the script stopped without changing anything."""
    assert result.returncode != 0
    assert _version(work) == '__version__ = "1.2.3"'
    assert _git(work, "rev-parse", "HEAD") == head_before
    assert "v1.2.4" not in _git(work, "tag", "--list")


def test_bump_refuses_unclean_tree():
    """Test that staged, modified, or untracked files stop the release."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        head = _git(work, "rev-parse", "HEAD")
        
        (work / "notes.txt").write_text("draft\n", encoding="utf-8")
        _assert_refused(work, _bump(work, "patch"), head)
        
        _git(work, "add", "notes.txt")
        _assert_refused(work, _bump(work, "patch"), head)
    print("✓ Bump refuses unclean tree test passed")


def test_bump_refuses_other_branch():
    """Test that releasing from a branch other than main is refused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "switch", "--quiet", "-c", "feature")
        head = _git(work, "rev-parse", "HEAD")
        
        _assert_refused(work, _bump(work, "patch"), head)
    print("✓ Bump refuses other branch test passed")


def test_bump_refuses_unpushed_commit():
    """Test that a local commit not on origin/main is refused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "commit", "--quiet", "--allow-empty", "-m", "unpushed")
        head = _git(work, "rev-parse", "HEAD")
        
        _assert_refused(work, _bump(work, "patch"), head)
    print("✓ Bump refuses unpushed commit test passed")


def test_bump_refuses_existing_tag():
    """Test that an existing tag for the new version is refused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "tag", "v1.2.4")
        _git(work, "push", "--quiet", "origin", "v1.2.4")
        _git(work, "tag", "--delete", "v1.2.4")
        head = _git(work, "rev-parse", "HEAD")
        
        result = _bump(work, "patch")
        
        assert result.returncode != 0
        assert _version(work) == '__version__ = "1.2.3"'
        assert _git(work, "rev-parse", "HEAD") == head
    print("✓ Bump refuses existing tag test passed")


def test_bump_refuses_invalid_arguments():
    """Test that an unknown bump type or extra flag prints usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        head = _git(work, "rev-parse", "HEAD")
        
        for args in (("build",), ("patch", "--force"), ()):
            result = _bump(work, *args)
            _assert_refused(work, result, head)
            assert "Usage" in result.stderr
    print("✓ Bump refuses invalid arguments test passed")


if __name__ == "__main__":
    print("Running bump_version tests...\n")
    
    test_bump_patch_commits_and_tags()
    test_bump_minor_and_major_reset_lower_parts()
    test_bump_with_push_sends_branch_and_tag()
    test_bump_refuses_unclean_tree()
    test_bump_refuses_other_branch()
    test_bump_refuses_unpushed_commit()
    test_bump_refuses_existing_tag()
    test_bump_refuses_invalid_arguments()
    
    print("\n✓ All bump_version tests passed!")
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `uv run python tests/test_bump_version.py`
Expected: FAIL（`test_bump_with_push_sends_branch_and_tag` で `AssertionError`。今のスクリプトは `--push` を受け付けず、`patch` 以外の引数を無視する）

- [ ] **Step 3: `scripts/bump_version.sh` を置き換える**

```bash
#!/bin/bash
# Bumps the package version, commits it, and tags the commit.
#
# Usage: scripts/bump_version.sh {major|minor|patch} [--push]
#
# With --push, sends main and the new tag to origin in one atomic push,
# which triggers the release workflow.

set -euo pipefail

readonly VERSION_FILE="src/enecoq_data_fetcher/__init__.py"
readonly RELEASE_BRANCH="main"

die() {
  echo "Error: $*" >&2
  exit 1
}

usage() {
  echo "Usage: $0 {major|minor|patch} [--push]" >&2
  exit 1
}

cd "$(dirname "$0")/.."

[[ $# -eq 1 || $# -eq 2 ]] || usage
bump_type="$1"
push=false
if [[ $# -eq 2 ]]; then
  [[ "$2" == "--push" ]] || usage
  push=true
fi

current_version=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$VERSION_FILE")
[[ "$current_version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]] \
  || die "Unexpected version in $VERSION_FILE: '$current_version'"
major="${BASH_REMATCH[1]}"
minor="${BASH_REMATCH[2]}"
patch="${BASH_REMATCH[3]}"

case "$bump_type" in
  major) new_version="$((major + 1)).0.0" ;;
  minor) new_version="$major.$((minor + 1)).0" ;;
  patch) new_version="$major.$minor.$((patch + 1))" ;;
  *) usage ;;
esac
readonly tag="v$new_version"

# Refuse to release anything but a clean, pushed main, so the release commit
# contains only the version change and the tag points at published history.
[[ -z "$(git status --porcelain)" ]] \
  || die "Working tree has uncommitted or untracked files"
[[ "$(git symbolic-ref --quiet --short HEAD || true)" == "$RELEASE_BRANCH" ]] \
  || die "Releases must be made from $RELEASE_BRANCH"
git fetch --quiet origin "$RELEASE_BRANCH"
[[ "$(git rev-parse HEAD)" == "$(git rev-parse "origin/$RELEASE_BRANCH")" ]] \
  || die "$RELEASE_BRANCH is not in sync with origin/$RELEASE_BRANCH"
! git rev-parse --quiet --verify "refs/tags/$tag" >/dev/null \
  || die "Tag $tag already exists locally"
[[ -z "$(git ls-remote --tags origin "refs/tags/$tag")" ]] \
  || die "Tag $tag already exists on origin"

echo "Bumping version from $current_version to $new_version"
sed -i.bak "s/^__version__ = \"$current_version\"$/__version__ = \"$new_version\"/" \
  "$VERSION_FILE"
rm "$VERSION_FILE.bak"

git commit --quiet -m "chore: bump version to $new_version" -- "$VERSION_FILE"
git tag "$tag"
echo "Created commit and tag $tag"

if [[ "$push" == true ]]; then
  git push --atomic origin "$RELEASE_BRANCH" "refs/tags/$tag"
else
  echo "Run 'git push --atomic origin $RELEASE_BRANCH refs/tags/$tag' to publish"
fi
```

- [ ] **Step 4: `Makefile` を置き換える**

```make
.PHONY: help release-patch release-minor release-major

help:
	@echo "Available commands:"
	@echo "  make release-patch  - Bump patch version (x.x.1) and push"
	@echo "  make release-minor  - Bump minor version (x.1.0) and push"
	@echo "  make release-major  - Bump major version (1.0.0) and push"

release-patch:
	@./scripts/bump_version.sh patch --push

release-minor:
	@./scripts/bump_version.sh minor --push

release-major:
	@./scripts/bump_version.sh major --push
```

- [ ] **Step 5: テストが通ることを確認する**

Run: `uv run python tests/test_bump_version.py && bash -n scripts/bump_version.sh`
Expected: PASS（`✓ All bump_version tests passed!`、構文エラーなし）

- [ ] **Step 6: `tests/run_tests.sh` にテストを登録する**

`tests/run_tests.sh` の `run_suite "CLI" tests/test_cli.py` の次の行に追加する。

```bash
run_suite "Release script" tests/test_bump_version.py
```

Run: `./tests/run_tests.sh 2>&1 | grep "Release script"`
Expected: `✓ Release script tests passed`

- [ ] **Step 7: コミットする**

```bash
git add scripts/bump_version.sh Makefile tests/test_bump_version.py tests/run_tests.sh
git commit -m "fix(release): check repository state before bumping the version" -m "The script committed whatever else was staged and ran on any branch, and make pushed every local tag. It now refuses an unclean tree, a branch other than main, a main that differs from origin, and an existing tag, commits only the version file, and pushes main with just the new tag atomically when given --push."
```

---

### Task 9: ドキュメントと全体の確認

**Files:**
- Modify: `README.md`（JSON 出力例、設定ファイルの説明）
- Modify: `AGENTS.md`（リリースの説明）

**Interfaces:**
- Consumes: Task 1〜8 の変更後の挙動

- [ ] **Step 1: README の JSON 例を直す**

`README.md` の「### JSON」節の `"timestamp": "2024-01-15T10:30:00.123456",` を次に置き換える。

```json
  "timestamp": "2024-01-15T10:30:00.123456+09:00",
```

その直後の段落を次に置き換える。

```markdown
JSON には単位が含まれません。`usage` は kWh、`cost` は円（JPY）、`co2` は kg です。値は期間の開始からの累計です。`timestamp` は取得した時刻で、実行環境のタイムゾーンのオフセットが付きます。
```

- [ ] **Step 2: README の設定ファイルの説明を直す**

「## 設定ファイル」節の「コマンドライン引数と設定ファイルの両方で指定した場合は、コマンドライン引数が優先されます。」の直前に次の段落を追加する。

```markdown
`max_retries` は、取得に失敗したときに最初の試行に追加でやり直す回数です（`0` でやり直しなし）。`--config` で指定したファイルが存在しない場合や、値の型が正しくない場合、知らない項目がある場合はエラーになります。
```

- [ ] **Step 3: AGENTS.md のリリースの説明を直す**

`AGENTS.md` の「`make release-patch`, `make release-minor`, and `make release-major` tag and push, and CI then publishes to PyPI, so run them only when asked.」を次に置き換える。

```markdown
`make release-patch`, `make release-minor`, and `make release-major` run `scripts/bump_version.sh` with `--push`: they require a clean `main` in sync with origin, tag, and push, and CI then publishes to PyPI, so run them only when asked.
```

- [ ] **Step 4: 全テストと脆弱性スキャンを実行する**

Run: `./tests/run_tests.sh 2>&1 | tail -15`
Expected: 最後に `✓ All test suites passed!`（終了コード 0）

Run: `osv-scanner --lockfile=uv.lock`
Expected: `No issues found`

- [ ] **Step 5: コミットする**

```bash
git add README.md AGENTS.md
git commit -m "docs: describe timestamp offset, retries, and release checks" -m "Update the JSON example for the UTC offset in timestamp, explain max_retries and config validation, and note the checks the release targets now perform."
```
