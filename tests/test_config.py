"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

from enecoq_data_fetcher import config


def test_default_config():
    """Test default configuration values."""
    cfg = config.Config()
    
    assert cfg.log_level == "INFO"
    assert cfg.log_file is None  # No file logging by default
    assert cfg.timeout == 30
    assert cfg.max_retries == 3
    assert "Mozilla" in cfg.user_agent
    
    print("✓ Default config test passed")


def test_config_to_dict():
    """Test configuration to dictionary conversion."""
    cfg = config.Config()
    cfg_dict = cfg.to_dict()
    
    assert isinstance(cfg_dict, dict)
    assert cfg_dict["log_level"] == "INFO"
    assert cfg_dict["timeout"] == 30
    assert cfg_dict["max_retries"] == 3
    
    print("✓ Config to_dict test passed")


def test_config_load_without_file():
    """Test loading configuration without a file."""
    cfg = config.Config.load(config_path=None, log_level="DEBUG")
    
    # Should use defaults except for overridden values
    assert cfg.log_level == "DEBUG"
    assert cfg.timeout == 30
    assert cfg.max_retries == 3
    
    print("✓ Config load without file test passed")


def test_config_load_with_nonexistent_file():
    """Test loading configuration with non-existent file."""
    try:
        config.Config.load(
            config_path="/nonexistent/config.yaml",
            log_level="WARNING"
        )
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass
    
    print("✓ Config load with nonexistent file test passed")


def test_config_from_yaml_file():
    """Test loading configuration from YAML file."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write("""
log_level: DEBUG
log_file: custom/path.log
timeout: 60
max_retries: 5
user_agent: "Custom User Agent"
""")
        temp_path = f.name
    
    try:
        # Load config from file
        cfg = config.Config.from_file(temp_path)
        
        assert cfg.log_level == "DEBUG"
        assert cfg.log_file == "custom/path.log"
        assert cfg.timeout == 60
        assert cfg.max_retries == 5
        assert cfg.user_agent == "Custom User Agent"
        
        print("✓ Config from YAML file test passed")
        
    finally:
        # Clean up
        os.unlink(temp_path)


def test_config_load_with_yaml_and_override():
    """Test loading configuration from YAML with command-line override."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write("""
log_level: DEBUG
timeout: 60
max_retries: 5
""")
        temp_path = f.name
    
    try:
        # Load config with override
        cfg = config.Config.load(
            config_path=temp_path,
            log_level="ERROR"
        )
        
        # log_level should be overridden
        assert cfg.log_level == "ERROR"
        # Other values should come from file
        assert cfg.timeout == 60
        assert cfg.max_retries == 5
        
        print("✓ Config load with YAML and override test passed")
        
    finally:
        # Clean up
        os.unlink(temp_path)


def test_config_from_file_not_found():
    """Test loading configuration from non-existent file."""
    try:
        config.Config.from_file("/nonexistent/config.yaml")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert "not found" in str(e)
        print("✓ Config from_file not found test passed")


def _write_temp_config(content):
    """Write content to a temporary YAML file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(content)
        return f.name


def test_config_from_file_invalid_values():
    """Test that invalid config files are rejected."""
    cases = [
        "log_level: VERBOSE\n",
        "timeout: thirty\n",
        "timeout: 0\n",
        "max_retries: -1\n",
        "max_retries: true\n",
        "unknown_key: 1\n",
        "- not\n- a mapping\n",
        "log_level: [unclosed\n",
    ]
    for content in cases:
        temp_path = _write_temp_config(content)
        try:
            config.Config.from_file(temp_path)
            assert False, "Should have raised ValueError for %r" % content
        except ValueError:
            pass
        finally:
            os.unlink(temp_path)
    
    print("✓ Config from_file invalid values test passed")


def test_config_from_empty_file():
    """Test that an empty config file yields defaults."""
    temp_path = _write_temp_config("")
    try:
        cfg = config.Config.from_file(temp_path)
        assert cfg == config.Config()
    finally:
        os.unlink(temp_path)
    
    print("✓ Config from empty file test passed")


def test_config_log_level_normalized():
    """Test that log levels are normalized to upper case."""
    assert config.Config(log_level="debug").log_level == "DEBUG"
    cfg = config.Config.load(log_level="warning", log_file="app.log")
    assert cfg.log_level == "WARNING"
    assert cfg.log_file == "app.log"
    
    print("✓ Config log level normalized test passed")

if __name__ == "__main__":
    print("Running configuration tests...\n")
    
    test_default_config()
    test_config_to_dict()
    test_config_load_without_file()
    test_config_load_with_nonexistent_file()
    test_config_from_yaml_file()
    test_config_load_with_yaml_and_override()
    test_config_from_file_not_found()
    test_config_from_file_invalid_values()
    test_config_from_empty_file()
    test_config_log_level_normalized()
    
    print("\n✓ All configuration tests passed!")
