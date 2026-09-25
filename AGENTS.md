# AGENTS.md

## Product

enecoQ Data Fetcher is a CLI that fetches power usage, cost, and CO2 emissions from enecoQ, the power data service inside Family Net Japan's CYBERHOME. enecoQ has no public API, so the tool scrapes it with Playwright.

The JSON output keys are a contract: users parse them from cron jobs and Home Assistant sensors, so do not rename or remove them.

Everything written to stdout, JSON, or unit attributes of the data models is English (`JPY`, not `円`), because Japanese text in these outputs gets garbled on some terminals and consumers. Credentials must never reach logs.

## Scraping

Selectors and element IDs must come from the live enecoQ pages, not from guesses: inspect the actual HTML with a browser automation tool before writing or changing a selector. When a page needs a login, ask for the enecoQ credentials in the chat; they are not stored in the repository.

## Development

Use uv, not pip. Tests do not use pytest: run all of them with `./tests/run_tests.sh`, or one file with `PYTHONPATH=src uv run python tests/test_fetcher.py`. Each test file must run its own tests from an `if __name__ == "__main__":` block, because that is how `run_tests.sh` invokes it.

`make release-patch`, `make release-minor`, and `make release-major` run `scripts/bump_version.sh` with `--push`: they require a clean `main` in sync with origin, tag, and push, and CI then publishes to PyPI, so run them only when asked.

Follow the Google Python Style Guide, including its rule to import modules rather than individual classes or functions (`from enecoq_data_fetcher import fetcher`, then `fetcher.fetch_data()`).

## Dependencies and security

Aikido Safe Chain cannot enforce a minimum package age for Python, so check it by hand: a new dependency or version must be at least 96 hours old, actively maintained, and free of known vulnerabilities. Before committing a dependency change, run `osv-scanner --lockfile=uv.lock` and the tests. Keep the Safe Chain and OSV-Scanner jobs in `.github/workflows/security-scan.yml` intact.

Report vulnerabilities in this project through a GitHub Security Advisory, not a public issue.

## Commits

Include a body that explains what changed and why. Use the module name (`authenticator`, `cli`, `config`, `controller`, `exceptions`, `exporter`, `fetcher`, `logger`, `models`) as the Conventional Commits scope.
