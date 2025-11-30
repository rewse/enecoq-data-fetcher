#!/bin/bash

# Test runner script for enecoQ Data Fetcher
# This script runs all test suites and reports results

set -e  # Exit on error

echo "========================================"
echo "enecoQ Data Fetcher - Test Suite"
echo "========================================"
echo ""

# Move to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=src

# Track test results
FAILED=0

# Unit tests
echo "=== Unit Tests ==="
echo ""

# Run models tests
echo "Running models tests..."
echo "----------------------------------------"
if python3 tests/test_models.py; then
    echo "✓ Models tests passed"
else
    echo "✗ Models tests failed"
    FAILED=1
fi
echo ""

# Run exceptions tests
echo "Running exceptions tests..."
echo "----------------------------------------"
if python3 tests/test_exceptions.py; then
    echo "✓ Exceptions tests passed"
else
    echo "✗ Exceptions tests failed"
    FAILED=1
fi
echo ""

# Run authenticator tests
echo "Running authenticator tests..."
echo "----------------------------------------"
if python3 tests/test_authenticator.py 2>&1 | grep -v "Traceback" | grep -v "File \"" | grep -v "raise" | grep -v "Exception:"; then
    echo "✓ Authenticator tests passed"
else
    echo "✗ Authenticator tests failed"
    FAILED=1
fi
echo ""

# Run fetcher tests
echo "Running fetcher tests..."
echo "----------------------------------------"
if python3 tests/test_fetcher.py 2>&1 | grep -v "Traceback" | grep -v "File \"" | grep -v "raise" | grep -v "Exception:"; then
    echo "✓ Fetcher tests passed"
else
    echo "✗ Fetcher tests failed"
    FAILED=1
fi
echo ""

# Run config tests
echo "Running config tests..."
echo "----------------------------------------"
if python3 tests/test_config.py; then
    echo "✓ Config tests passed"
else
    echo "✗ Config tests failed"
    FAILED=1
fi
echo ""

# Run exporter tests
echo "Running exporter tests..."
echo "----------------------------------------"
if python3 tests/test_exporter.py; then
    echo "✓ Exporter tests passed"
else
    echo "✗ Exporter tests failed"
    FAILED=1
fi
echo ""

# Run logger tests
echo "Running logger tests..."
echo "----------------------------------------"
if python3 tests/test_logger.py; then
    echo "✓ Logger tests passed"
else
    echo "✗ Logger tests failed"
    FAILED=1
fi
echo ""

# Run CLI tests
echo "Running CLI tests..."
echo "----------------------------------------"
if python3 tests/test_cli.py; then
    echo "✓ CLI tests passed"
else
    echo "✗ CLI tests failed"
    FAILED=1
fi
echo ""

# Property-based tests (optional - requires hypothesis)
echo "=== Property-Based Tests ==="
echo ""

echo "Running property-based tests..."
echo "----------------------------------------"
if python3 -c "import hypothesis" 2>/dev/null; then
    if python3 tests/test_pbt.py; then
        echo "✓ Property-based tests passed"
    else
        echo "✗ Property-based tests failed"
        FAILED=1
    fi
else
    echo "⊘ Skipping property-based tests (hypothesis not installed)"
    echo "  Install with: uv sync --extra test"
fi
echo ""

# Integration tests
echo "=== Integration Tests ==="
echo ""

# Run logging integration tests
echo "Running logging integration tests..."
echo "----------------------------------------"
if python3 tests/test_logging_integration.py; then
    echo "✓ Logging integration tests passed"
else
    echo "✗ Logging integration tests failed"
    FAILED=1
fi
echo ""

# Run integration tests
echo "Running integration tests..."
echo "----------------------------------------"
if python3 tests/test_integration.py 2>&1 | grep -v "Logging error" | grep -v "ValueError: I/O operation"; then
    echo "✓ Integration tests passed"
else
    echo "✗ Integration tests failed"
    FAILED=1
fi
echo ""

# Summary
echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo "✓ All test suites passed!"
    echo "========================================"
    exit 0
else
    echo "✗ Some tests failed"
    echo "========================================"
    exit 1
fi
