"""
Unit tests for configuration module.
"""

import os

from src.utils.config import SecretsManager
from src.utils.config import load_config


class TestSecretsManager:
    """Test SecretsManager functionality."""

    def test_encrypt_decrypt_secret(self):
        """Test secret encryption and decryption."""
        manager = SecretsManager()
        secret = "test-secret-123"

        # Encrypt the secret
        encrypted = manager.encrypt_secret(secret)
        assert encrypted != secret
        assert len(encrypted) > 0

        # Decrypt the secret
        decrypted = manager.decrypt_secret(encrypted)
        assert decrypted == secret

    def test_generate_secret(self):
        """Test secret generation."""
        manager = SecretsManager()

        # Generate secret with default length
        secret1 = manager.generate_secret()
        assert len(secret1) > 0

        # Generate secret with custom length
        secret2 = manager.generate_secret(16)
        assert len(secret2) > 0

        # Secrets should be different
        assert secret1 != secret2


class TestConfig:
    """Test configuration loading and validation."""

    def test_load_config_with_env_vars(self):
        """Test loading configuration with environment variables."""
        # Set test environment variables
        test_env = {
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "DEBUG",
            "MODEL_SERVICE_URL": "http://test:8001",
            "AUTH_SECRET_KEY": "test-secret-key",
        }

        # Temporarily set environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            config = load_config()
            assert config.environment == "test"
            assert config.logging.level == "DEBUG"
            assert config.model.service_url == "http://test:8001"
            assert config.auth.secret_key == "test-secret-key"
        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    def test_config_validation(self):
        """Test configuration validation."""
        # This should not raise any errors with valid config
        config = load_config()
        assert config is not None
        assert config.environment in ["development", "staging", "production"]

    def test_config_dataclass_structure(self):
        """Test that config has expected structure."""
        config = load_config()

        # Check main sections exist
        assert hasattr(config, "discord")
        assert hasattr(config, "model")
        assert hasattr(config, "rag")
        assert hasattr(config, "agent")
        assert hasattr(config, "security")
        assert hasattr(config, "logging")
        assert hasattr(config, "database")
        assert hasattr(config, "web_chat")
        assert hasattr(config, "auth")
        assert hasattr(config, "tunnel")

        # Check some key properties
        assert hasattr(config.web_chat, "host")
        assert hasattr(config.web_chat, "port")
        assert hasattr(config.auth, "secret_key")
        assert hasattr(config.tunnel, "service")
