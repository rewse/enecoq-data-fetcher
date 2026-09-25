# AGENTS.md

## Product

enecoQ Data Fetcher is a CLI that logs in to enecoQ, the power data service inside Family Net Japan's CYBERHOME, and retrieves power usage (kWh), cost (JPY), and CO2 emissions (kg) for today or the current month. Users are CYBERHOME account holders and developers who want to analyze the data or feed it into energy-management systems. enecoQ has no public API, so the tool drives a real browser with Playwright.

Output is either JSON or a console report. The JSON shape is part of the tool's contract:

```json
{
  "period": "month",
  "timestamp": "2024-01-15T10:30:00",
  "usage": 250.5,
  "cost": 7515.0,
  "co2": 125.25
}
```

Everything written to stdout, JSON, or unit attributes of the data models is English (`JPY`, not `円`), because Japanese text in these outputs gets garbled on some terminals and consumers.

Credentials must never reach logs. Logging goes to the console at INFO by default; file logging happens only when `--log-file` or `log_file` in `config.yaml` is set.

## Architecture

Code lives in `src/enecoq_data_fetcher/`, with one module per responsibility:

- `authenticator.py`: logs in to enecoQ and manages the session
- `cli.py`: Click entry point and argument validation
- `config.py`: loads `config.yaml` (see `config.yaml.example` for the keys)
- `controller.py`: coordinates the components
- `exceptions.py`, `logger.py`, `models.py`: custom exceptions, logging setup, data models
- `exporter.py`: formats and writes output
- `fetcher.py`: scrapes the data pages with Playwright

Keep new code within this split rather than adding cross-cutting logic to `cli.py` or `controller.py`. The package ships `py.typed`, so public APIs need type annotations. Save generated data under `data/` or `output/`, which are gitignored.

## Scraping with Playwright

Selectors and element IDs must come from the live enecoQ pages, not from guesses: inspect the actual HTML with the Playwright MCP server (configured in `.kiro/settings/mcp.json`) before writing or changing a selector. When a page needs a login, ask for the enecoQ credentials in the chat; they are not stored in the repository.

## Development

Use uv for everything; the supported Python range is in `pyproject.toml` (`requires-python`) and the local version in `.python-version`.

```bash
uv sync
uv run playwright install
uv run enecoq-data-fetcher --help
uv build
```

Run the full test suite with `./tests/run_tests.sh`. To run one file, set `PYTHONPATH=src` and run it directly, for example `PYTHONPATH=src uv run python tests/test_fetcher.py`. Tests follow these conventions, which `run_tests.sh` relies on:

- Tests live in `tests/` as `test_*.py` and import the package as `from enecoq_data_fetcher import module_name`.
- Each file runs all of its tests from an `if __name__ == "__main__":` block, and each test function runs independently.
- `test_pbt.py` uses Hypothesis (the `test` extra) and is skipped when it is not installed.

Releases go through `make release-patch`, `make release-minor`, or `make release-major`. Each one bumps the version in `src/enecoq_data_fetcher/__init__.py`, commits, tags, and pushes; GitHub Actions then creates the GitHub Release and publishes to PyPI. Because these push to the remote, run them only when asked. Details are in `.github/RELEASE.md`.

## Python style

Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html). The rules most often missed in this codebase:

- Import packages and modules only, never individual classes or functions; types from `typing`, `collections.abc`, and `typing_extensions` are the exception. Write `from enecoq_data_fetcher import fetcher` and call `fetcher.fetch_data()`.
- Pass logging arguments separately (`log.info('Version: %s', version)`) instead of using f-strings in log calls.
- Catch specific exceptions rather than bare `except:` or `Exception`, keep `try` blocks small, and do not use `assert` for runtime checks.
- Keep lines within 80 characters, and give public APIs docstrings with `Args`, `Returns`, and `Raises` sections.

## Supply-chain security

The project defends against malicious Python packages in three layers, and changes to dependencies or CI must keep all three intact.

1. Aikido Safe Chain blocks known malware at install time. CI installs it in `.github/workflows/security-scan.yml`. For local development, install it with Python support (`curl -fsSL https://raw.githubusercontent.com/AikidoSec/safe-chain/main/install-scripts/install-safe-chain.sh | sh -s -- --include-python`), restart the terminal, and confirm that `uv pip install safe-chain-pi-test` is blocked. Its minimum-package-age check covers only npm-family managers, not uv or pip.
2. Run the app with least privilege: a normal user (never `sudo`) inside the uv-managed `.venv`.
3. OSV-Scanner runs in CI for known vulnerabilities. Locally, run `osv-scanner --lockfile=uv.lock`.

Because Safe Chain cannot enforce a package age for Python, check it by hand. Before adding a dependency, confirm it was published at least 96 hours ago, is actively maintained, has meaningful adoption, and has no known vulnerabilities. Before updating one, read its changelog, run OSV-Scanner, and run the tests.

Report a vulnerability in this project through a GitHub Security Advisory (Security tab, then Report a vulnerability), not a public issue. When a dependency has a vulnerability, assess the impact, update to a fixed version if one exists or look for an alternative package if not, and notify users.

## Commits

Follow Conventional Commits and include a body that explains what changed, why, and what it affects. Use the module name as the scope: `authenticator`, `cli`, `config`, `controller`, `exceptions`, `exporter`, `fetcher`, `logger`, or `models`.
