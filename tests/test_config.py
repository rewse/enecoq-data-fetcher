"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

from enecoq_data_fetcher import config


def test_default_config():
    """Test default configuration values."""
    cfg = config.Config()
    
    assert cfg.log_level == "INFO"
    assert cfg.log_file == "logs/enecoq.log"
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
    cfg = config.Config.load(
        config_path="/nonexistent/config.yaml",
        log_level="WARNING"
    )
    
    # Should use defaults with command-line overrides
    assert cfg.log_level == "WARNING"
    assert cfg.timeout == 30
    
    print("✓ Config load with nonexistent file test passed")


def test_config_from_yaml_file():
    """Test loading configuration from YAML file."""
    # Skip if PyYAML is not available
    if not config.YAML_AVAILABLE:
        print("⊘ Skipping YAML test (PyYAML not installed)")
        return
    
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
    # Skip if PyYAML is not available
    if not config.YAML_AVAILABLE:
        print("⊘ Skipping YAML override test (PyYAML not installed)")
        return
    
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
    # Skip if PyYAML is not available
    if not config.YAML_AVAILABLE:
        print("⊘ Skipping file not found test (PyYAML not installed)")
        return
    
    try:
        config.Config.from_file("/nonexistent/config.yaml")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert "not found" in str(e)
        print("✓ Config from_file not found test passed")


def test_config_without_yaml_library():
    """Test configuration behavior when PyYAML is not available."""
    # Temporarily disable YAML
    original_yaml_available = config.YAML_AVAILABLE
    config.YAML_AVAILABLE = False
    
    try:
        # Should raise ValueError when trying to load from file
        try:
            config.Config.from_file("config.yaml")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "PyYAML" in str(e)
            print("✓ Config without YAML library test passed")
    finally:
        # Restore original state
        config.YAML_AVAILABLE = original_yaml_available


if __name__ == "__main__":
    print("Running configuration tests...\n")
    
    test_default_config()
    test_config_to_dict()
    test_config_load_without_file()
    test_config_load_with_nonexistent_file()
    test_config_from_yaml_file()
    test_config_load_with_yaml_and_override()
    test_config_from_file_not_found()
    test_config_without_yaml_library()
    
    print("\n✓ All configuration tests passed!")
