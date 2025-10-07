"""
Configuration management for Jerry AI assistant.

This module handles loading and managing configuration settings
from environment variables and configuration files with secure
secrets management.
"""

import base64
import os
import secrets
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from dotenv import load_dotenv


class SecretsManager:
    """Secure secrets management for sensitive configuration values."""

    def __init__(self, encryption_key: str | None = None):
        """Initialize secrets manager with encryption key.

        Args:
            encryption_key: Base64-encoded encryption key (generated if None)
        """
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode())
        else:
            # Generate a new key for development
            key = Fernet.generate_key()
            self.fernet = Fernet(key)
            # Store key for reference in development
            self._dev_key = base64.b64encode(key).decode()

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value.

        Args:
            secret: Plain text secret to encrypt

        Returns:
            Base64-encoded encrypted secret
        """
        encrypted = self.fernet.encrypt(secret.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret value.

        Args:
            encrypted_secret: Base64-encoded encrypted secret

        Returns:
            Decrypted plain text secret
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_secret.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            # If decryption fails, assume it's already plain text (for development)
            return encrypted_secret

    def generate_secret(self, length: int = 32) -> str:
        """Generate a cryptographically secure random secret.

        Args:
            length: Length of the secret in bytes

        Returns:
            Base64-encoded random secret
        """
        random_bytes = secrets.token_bytes(length)
        return base64.b64encode(random_bytes).decode()


def get_env_secret(
    key: str, default: Any = None, secrets_manager: SecretsManager | None = None
) -> str:
    """Get an environment variable that may be encrypted.

    Args:
        key: Environment variable name
        default: Default value if not found
        secrets_manager: Optional secrets manager for decryption

    Returns:
        Decrypted secret value
    """
    value = os.getenv(key, default)
    if value and secrets_manager and value.startswith("ENCRYPTED:"):
        # Remove prefix and decrypt
        encrypted_value = value[10:]  # Remove "ENCRYPTED:" prefix
        return secrets_manager.decrypt_secret(encrypted_value)
    return value


def validate_secrets_security():
    """Validate that security-critical secrets are properly configured."""
    errors = []

    # Check for default/weak secrets
    jwt_secret = os.getenv("JWT_SECRET", "")
    if jwt_secret in ["", "change-me-in-production", "secret", "jwt-secret"]:
        errors.append("JWT_SECRET must be set to a strong, unique value")

    encryption_key = os.getenv("ENCRYPTION_KEY", "")
    if encryption_key in ["", "change-me-in-production", "key", "encryption-key"]:
        errors.append("ENCRYPTION_KEY must be set to a strong, unique value")

    # discord_token = os.getenv("DISCORD_BOT_TOKEN", "")
    # if not discord_token:
    #     errors.append("DISCORD_BOT_TOKEN is required")

    # Check for accidentally committed secrets (basic patterns)
    if jwt_secret and len(jwt_secret) < 32:
        errors.append("JWT_SECRET should be at least 32 characters long")

    if encryption_key and len(encryption_key) < 32:
        errors.append("ENCRYPTION_KEY should be at least 32 characters long")

    return errors


@dataclass
class DiscordConfig:
    """Discord bot configuration."""

    bot_token: str
    guild_id: str | None = None
    command_prefix: str = "!"
    welcome_enabled: bool = True
    max_message_length: int = 2000


@dataclass
class ModelConfig:
    """AI model configuration."""

    service_url: str = "http://localhost:8001"
    model_name: str = "llama-3.1-8b-instruct"
    quantization: str = "Q4_K_M"
    context_length: int = 4096
    temperature: float = 0.7
    max_tokens: int = 512
    timeout_seconds: int = 30


@dataclass
class RAGConfig:
    """RAG service configuration."""

    service_url: str = "http://localhost:8002"
    vector_db_path: str = "./data/vector_db"
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_results: int = 5
    similarity_threshold: float = 0.7


@dataclass
class AgentConfig:
    """Agent service configuration."""

    service_url: str = "http://localhost:8003"
    langchain_api_key: str | None = None
    langsmith_project: str | None = None
    max_conversation_length: int = 20
    summarization_threshold: int = 15


@dataclass
class SecurityConfig:
    """Security configuration."""

    jwt_secret: str
    encryption_key: str
    token_expiry_hours: int = 24
    rate_limit_per_minute: int = 60
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])

    # Additional security settings
    enable_cors: bool = True
    secure_cookies: bool = True
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    require_https: bool = False  # Set to True in production
    api_key_header: str = "X-API-Key"

    # Secrets encryption
    secrets_encryption_enabled: bool = True
    rotate_secrets_days: int = 90


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False
    file_path: str | None = None
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class WebChatConfig:
    """Web chat service configuration."""

    host: str = "0.0.0.0"
    port: int = 8004
    allowed_hosts: list[str] = field(default_factory=lambda: ["*"])
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    tunnel_enabled: bool = True
    tunnel_service: str = "cloudflare"  # cloudflare, ngrok, etc.
    session_timeout_minutes: int = 60


@dataclass
class AuthConfig:
    """Authentication configuration."""

    secret_key: str | None = None
    algorithm: str = "HS256"
    token_expiry_hours: int = 24
    max_sessions_per_user: int = 5
    cloudflare_team_domain: str | None = None
    cloudflare_audience_tag: str | None = None
    admin_emails: list[str] = field(default_factory=list)


@dataclass
class TunnelConfig:
    """Tunnel service configuration."""

    service: str = "cloudflare"  # cloudflare, ngrok
    cloudflare_tunnel_token: str | None = None
    cloudflare_tunnel_id: str | None = None
    ngrok_auth_token: str | None = None
    custom_domain: str | None = None


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "sqlite:///./data/jerry.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class Config:
    """Main configuration class."""

    discord: DiscordConfig
    model: ModelConfig
    rag: RAGConfig
    agent: AgentConfig
    security: SecurityConfig
    logging: LoggingConfig
    database: DatabaseConfig
    web_chat: WebChatConfig
    auth: AuthConfig
    tunnel: TunnelConfig

    # Environment settings
    environment: str = "development"
    debug: bool = False
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    logs_dir: Path = field(default_factory=lambda: Path("./logs"))


def load_config(env_file: str | None = None) -> Config:
    """Load configuration from environment variables and .env file."""
    # Load environment variables from .env file
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Initialize secrets manager for secure configuration
    encryption_key = os.getenv("ENCRYPTION_KEY")
    secrets_manager = SecretsManager(encryption_key) if encryption_key else None

    # Helper function to get environment variable with type conversion
    def get_env(
        key: str, default: Any = None, var_type: type = str, is_secret: bool = False
    ) -> Any:
        if is_secret:
            value = get_env_secret(key, default, secrets_manager)
        else:
            value = os.getenv(key, default)

        if value is None:
            return None

        if var_type is bool:
            return str(value).lower() in ("true", "1", "yes", "on")
        if var_type is int:
            try:
                return int(value)
            except ValueError:
                return default
        elif var_type is float:
            try:
                return float(value)
            except ValueError:
                return default
        elif var_type is list:
            return [item.strip() for item in str(value).split(",") if item.strip()]

        return value

    # Discord configuration
    discord_config = DiscordConfig(
        bot_token=get_env("DISCORD_BOT_TOKEN", "", str, True),  # Secret
        guild_id=get_env("DISCORD_GUILD_ID"),
        command_prefix=get_env("DISCORD_COMMAND_PREFIX", "!"),
        welcome_enabled=get_env("DISCORD_WELCOME_ENABLED", True, bool),
        max_message_length=get_env("DISCORD_MAX_MESSAGE_LENGTH", 2000, int),
    )

    # Model configuration
    model_config = ModelConfig(
        service_url=get_env("MODEL_SERVICE_URL", "http://localhost:8001"),
        model_name=get_env("MODEL_NAME", "llama-3.1-8b-instruct"),
        quantization=get_env("MODEL_QUANTIZATION", "Q4_K_M"),
        context_length=get_env("MODEL_CONTEXT_LENGTH", 4096, int),
        temperature=get_env("MODEL_TEMPERATURE", 0.7, float),
        max_tokens=get_env("MODEL_MAX_TOKENS", 512, int),
        timeout_seconds=get_env("MODEL_TIMEOUT_SECONDS", 30, int),
    )

    # RAG configuration
    rag_config = RAGConfig(
        service_url=get_env("RAG_SERVICE_URL", "http://localhost:8002"),
        vector_db_path=get_env("VECTOR_DB_PATH", "./data/vector_db"),
        chunk_size=get_env("RAG_CHUNK_SIZE", 512, int),
        chunk_overlap=get_env("RAG_CHUNK_OVERLAP", 50, int),
        max_results=get_env("RAG_MAX_RESULTS", 5, int),
        similarity_threshold=get_env("RAG_SIMILARITY_THRESHOLD", 0.7, float),
    )

    # Agent configuration
    agent_config = AgentConfig(
        service_url=get_env("AGENT_SERVICE_URL", "http://localhost:8003"),
        langchain_api_key=get_env("LANGCHAIN_API_KEY", None, str, True),  # Secret
        langsmith_project=get_env("LANGSMITH_PROJECT"),
        max_conversation_length=get_env("AGENT_MAX_CONVERSATION_LENGTH", 20, int),
        summarization_threshold=get_env("AGENT_SUMMARIZATION_THRESHOLD", 15, int),
    )

    # Security configuration
    security_config = SecurityConfig(
        jwt_secret=get_env(
            "JWT_SECRET", "change-me-in-production", str, True
        ),  # Secret
        encryption_key=get_env(
            "ENCRYPTION_KEY", "change-me-in-production", str, True
        ),  # Secret
        token_expiry_hours=get_env("TOKEN_EXPIRY_HOURS", 24, int),
        rate_limit_per_minute=get_env("RATE_LIMIT_PER_MINUTE", 60, int),
        allowed_origins=get_env("ALLOWED_ORIGINS", ["*"], list),
        enable_cors=get_env("ENABLE_CORS", True, bool),
        secure_cookies=get_env("SECURE_COOKIES", True, bool),
        session_timeout_minutes=get_env("SESSION_TIMEOUT_MINUTES", 30, int),
        max_login_attempts=get_env("MAX_LOGIN_ATTEMPTS", 5, int),
        lockout_duration_minutes=get_env("LOCKOUT_DURATION_MINUTES", 15, int),
        require_https=get_env("REQUIRE_HTTPS", False, bool),
        api_key_header=get_env("API_KEY_HEADER", "X-API-Key"),
        secrets_encryption_enabled=get_env("SECRETS_ENCRYPTION_ENABLED", True, bool),
        rotate_secrets_days=get_env("ROTATE_SECRETS_DAYS", 90, int),
    )

    # Logging configuration
    logging_config = LoggingConfig(
        level=get_env("LOG_LEVEL", "INFO"),
        format=get_env(
            "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
        json_format=get_env("LOG_JSON_FORMAT", False, bool),
        file_path=get_env("LOG_FILE_PATH"),
        max_file_size_mb=get_env("LOG_MAX_FILE_SIZE_MB", 10, int),
        backup_count=get_env("LOG_BACKUP_COUNT", 5, int),
    )

    # Database configuration
    database_config = DatabaseConfig(
        url=get_env("DATABASE_URL", "sqlite:///./data/jerry.db"),
        echo=get_env("DATABASE_ECHO", False, bool),
        pool_size=get_env("DATABASE_POOL_SIZE", 5, int),
        max_overflow=get_env("DATABASE_MAX_OVERFLOW", 10, int),
    )

    # Web chat configuration
    web_chat_config = WebChatConfig(
        host=get_env("WEB_CHAT_HOST", "0.0.0.0"),
        port=get_env("WEB_CHAT_PORT", 8004, int),
        allowed_hosts=get_env("WEB_CHAT_ALLOWED_HOSTS", ["*"], list),
        cors_origins=get_env("WEB_CHAT_CORS_ORIGINS", ["*"], list),
        tunnel_enabled=get_env("WEB_CHAT_TUNNEL_ENABLED", True, bool),
        tunnel_service=get_env("WEB_CHAT_TUNNEL_SERVICE", "cloudflare"),
        session_timeout_minutes=get_env("WEB_CHAT_SESSION_TIMEOUT", 60, int),
    )

    # Auth configuration
    auth_config = AuthConfig(
        secret_key=get_env("AUTH_SECRET_KEY", None, str, True),  # Secret
        algorithm=get_env("AUTH_ALGORITHM", "HS256"),
        token_expiry_hours=get_env("AUTH_TOKEN_EXPIRY_HOURS", 24, int),
        max_sessions_per_user=get_env("AUTH_MAX_SESSIONS_PER_USER", 5, int),
        cloudflare_team_domain=get_env("CLOUDFLARE_TEAM_DOMAIN"),
        cloudflare_audience_tag=get_env("CLOUDFLARE_AUDIENCE_TAG"),
        admin_emails=get_env("AUTH_ADMIN_EMAILS", [], list),
    )

    # Tunnel configuration
    tunnel_config = TunnelConfig(
        service=get_env("TUNNEL_SERVICE", "cloudflare"),
        cloudflare_tunnel_token=get_env(
            "CLOUDFLARE_TUNNEL_TOKEN", None, str, True
        ),  # Secret
        cloudflare_tunnel_id=get_env("CLOUDFLARE_TUNNEL_ID"),
        ngrok_auth_token=get_env("NGROK_AUTH_TOKEN", None, str, True),  # Secret
        custom_domain=get_env("TUNNEL_CUSTOM_DOMAIN"),
    )

    # Main configuration
    config = Config(
        discord=discord_config,
        model=model_config,
        rag=rag_config,
        agent=agent_config,
        security=security_config,
        logging=logging_config,
        database=database_config,
        web_chat=web_chat_config,
        auth=auth_config,
        tunnel=tunnel_config,
        environment=get_env("ENVIRONMENT", "development"),
        debug=get_env("DEBUG", False, bool),
        data_dir=Path(get_env("DATA_DIR", "./data")),
        logs_dir=Path(get_env("LOGS_DIR", "./logs")),
    )

    # Validate required settings
    _validate_config(config)

    return config


def _validate_config(config: Config) -> None:
    """Validate configuration settings."""
    errors = []

    # Discord validation
    # if not config.discord.bot_token:
    #     errors.append("DISCORD_BOT_TOKEN is required")

    # Security validation
    security_errors = validate_secrets_security()
    errors.extend(security_errors)

    # Production-specific security checks
    if config.environment == "production":
        if not config.security.require_https:
            errors.append("REQUIRE_HTTPS should be enabled in production")

        if "*" in config.security.allowed_origins:
            errors.append("ALLOWED_ORIGINS should not include '*' in production")

        if not config.security.secure_cookies:
            errors.append("SECURE_COOKIES should be enabled in production")

    # Path validation
    try:
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create required directories: {e}")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


def create_env_template(output_path: str = ".env.example") -> None:
    """Create a template .env file with all configuration options."""
    template = """# Jerry AI Assistant Configuration

# Discord Bot Settings
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
DISCORD_COMMAND_PREFIX=!
DISCORD_WELCOME_ENABLED=true
DISCORD_MAX_MESSAGE_LENGTH=2000

# Model Service Settings
MODEL_SERVICE_URL=http://localhost:8001
MODEL_NAME=llama-3.1-8b-instruct
MODEL_QUANTIZATION=Q4_K_M
MODEL_CONTEXT_LENGTH=4096
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=512
MODEL_TIMEOUT_SECONDS=30

# RAG Service Settings
RAG_SERVICE_URL=http://localhost:8002
VECTOR_DB_PATH=./data/vector_db
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=50
RAG_MAX_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.7

# Agent Service Settings
AGENT_SERVICE_URL=http://localhost:8003
LANGCHAIN_API_KEY=optional_for_langsmith
LANGSMITH_PROJECT=optional_project_name
AGENT_MAX_CONVERSATION_LENGTH=20
AGENT_SUMMARIZATION_THRESHOLD=15

# Security Settings (CRITICAL: Change these in production!)
JWT_SECRET=generate_random_secret_here
ENCRYPTION_KEY=generate_32_byte_key_here
TOKEN_EXPIRY_HOURS=24
RATE_LIMIT_PER_MINUTE=60
ALLOWED_ORIGINS=*

# Additional Security Settings
ENABLE_CORS=true
SECURE_COOKIES=true
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
REQUIRE_HTTPS=false
API_KEY_HEADER=X-API-Key
SECRETS_ENCRYPTION_ENABLED=true
ROTATE_SECRETS_DAYS=90

# Logging Settings
LOG_LEVEL=INFO
LOG_JSON_FORMAT=false
LOG_FILE_PATH=./logs/jerry.log
LOG_MAX_FILE_SIZE_MB=10
LOG_BACKUP_COUNT=5

# Database Settings
DATABASE_URL=sqlite:///./data/jerry.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Environment Settings
ENVIRONMENT=development
DEBUG=false
DATA_DIR=./data
LOGS_DIR=./logs
"""

    Path(output_path).open("w").write(template)

    print(f"Created environment template at {output_path}")


def generate_production_secrets() -> dict[str, str]:
    """Generate secure secrets for production deployment.

    Returns:
        Dictionary of generated secrets
    """
    secrets_manager = SecretsManager()

    return {
        "JWT_SECRET": secrets_manager.generate_secret(32),
        "ENCRYPTION_KEY": secrets_manager.generate_secret(32),
        "API_KEY": secrets_manager.generate_secret(24),
    }


def encrypt_secrets_for_deployment(
    secrets_dict: dict[str, str], master_key: str
) -> dict[str, str]:
    """Encrypt secrets for secure deployment.

    Args:
        secrets_dict: Dictionary of plain text secrets
        master_key: Master encryption key

    Returns:
        Dictionary of encrypted secrets with ENCRYPTED: prefix
    """
    secrets_manager = SecretsManager(master_key)
    encrypted_secrets = {}

    for key, value in secrets_dict.items():
        encrypted_value = secrets_manager.encrypt_secret(value)
        encrypted_secrets[key] = f"ENCRYPTED:{encrypted_value}"

    return encrypted_secrets


# Global configuration instance
_config: Config | None = None


def get_config(reload: bool = False) -> Config:
    """Get the global configuration instance.

    Args:
        reload: Whether to reload configuration from environment

    Returns:
        Configuration instance
    """
    global _config

    if _config is None or reload:
        _config = load_config()

    return _config
