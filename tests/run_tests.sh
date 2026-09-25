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
