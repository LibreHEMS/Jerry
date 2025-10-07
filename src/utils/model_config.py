"""
Model configuration loader for Jerry AI.

This module handles loading and managing different model configurations,
including different quantizations and model variants.
"""

import json
from pathlib import Path

from ..services.model_service import ModelConfig
from ..services.model_service import ModelType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ModelConfigLoader:
    """Loads and manages model configurations."""

    def __init__(self, config_dir: str = "./configs/model_configs"):
        self.config_dir = Path(config_dir)
        self._configs: dict[str, ModelConfig] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """Load all model configurations from the config directory."""
        if not self.config_dir.exists():
            logger.warning(f"Model config directory does not exist: {self.config_dir}")
            self._create_default_configs()
            return

        # Load configuration files
        for config_file in self.config_dir.glob("*.json"):
            try:
                self._load_config_file(config_file)
            except Exception as e:
                logger.error(f"Failed to load config file {config_file}: {e}")

        # If no configs loaded, create defaults
        if not self._configs:
            logger.info("No model configurations found, creating defaults")
            self._create_default_configs()

    def _load_config_file(self, config_file: Path) -> None:
        """Load a single configuration file."""
        logger.info(f"Loading model config: {config_file}")

        with config_file.open() as f:
            data = json.load(f)

        # Handle single config or multiple configs in one file
        if isinstance(data, dict) and "name" in data:
            # Single config
            config = self._parse_config(data)
            self._configs[config.name] = config
        elif isinstance(data, dict) and "models" in data:
            # Multiple configs
            for model_data in data["models"]:
                config = self._parse_config(model_data)
                self._configs[config.name] = config
        elif isinstance(data, list):
            # List of configs
            for model_data in data:
                config = self._parse_config(model_data)
                self._configs[config.name] = config

    def _parse_config(self, data: dict) -> ModelConfig:
        """Parse a model configuration from JSON data."""
        return ModelConfig(
            name=data["name"],
            type=ModelType(data.get("type", "chat")),
            model_path=data["model_path"],
            context_length=data.get("context_length", 4096),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 512),
            top_p=data.get("top_p", 0.9),
            top_k=data.get("top_k", 40),
            repeat_penalty=data.get("repeat_penalty", 1.1),
            quantization=data.get("quantization", "Q4_K_M"),
            gpu_layers=data.get("gpu_layers", 0),
            threads=data.get("threads", 4),
        )

    def _create_default_configs(self) -> None:
        """Create default model configurations."""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        default_configs = [
            {
                "name": "llama-3.1-8b-instruct",
                "type": "chat",
                "model_path": "./models/llama-3.1-8b-instruct-q4_k_m.gguf",
                "context_length": 8192,
                "temperature": 0.7,
                "max_tokens": 512,
                "quantization": "Q4_K_M",
                "description": "Llama 3.1 8B Instruct model with Q4_K_M quantization",
            },
            {
                "name": "llama-3.1-8b-instruct-q6",
                "type": "chat",
                "model_path": "./models/llama-3.1-8b-instruct-q6_k.gguf",
                "context_length": 8192,
                "temperature": 0.7,
                "max_tokens": 512,
                "quantization": "Q6_K",
                "description": "Llama 3.1 8B Instruct model with Q6_K quantization (higher quality)",
            },
            {
                "name": "llama-3.1-8b-instruct-q2",
                "type": "chat",
                "model_path": "./models/llama-3.1-8b-instruct-q2_k.gguf",
                "context_length": 8192,
                "temperature": 0.7,
                "max_tokens": 512,
                "quantization": "Q2_K",
                "description": "Llama 3.1 8B Instruct model with Q2_K quantization (smaller, faster)",
            },
            {
                "name": "llama-3.1-70b-instruct",
                "type": "chat",
                "model_path": "./models/llama-3.1-70b-instruct-q4_k_m.gguf",
                "context_length": 8192,
                "temperature": 0.7,
                "max_tokens": 512,
                "quantization": "Q4_K_M",
                "gpu_layers": 32,
                "description": "Llama 3.1 70B Instruct model (requires significant RAM/VRAM)",
            },
        ]

        # Save default configs
        config_data = {"models": default_configs}
        config_file = self.config_dir / "default_models.json"

        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Created default model configs at: {config_file}")

        # Load the created configs
        for model_data in default_configs:
            config = self._parse_config(model_data)
            self._configs[config.name] = config

    def get_config(self, name: str) -> ModelConfig | None:
        """Get a model configuration by name."""
        return self._configs.get(name)

    def list_configs(self) -> list[str]:
        """List all available model configuration names."""
        return list(self._configs.keys())

    def get_configs_by_quantization(self, quantization: str) -> list[ModelConfig]:
        """Get all configurations for a specific quantization level."""
        return [
            config
            for config in self._configs.values()
            if config.quantization == quantization
        ]

    def get_configs_by_model_family(self, family: str) -> list[ModelConfig]:
        """Get all configurations for a model family (e.g., 'llama-3.1')."""
        return [
            config
            for config in self._configs.values()
            if family.lower() in config.name.lower()
        ]

    def add_config(self, config: ModelConfig, save: bool = True) -> None:
        """Add a new model configuration."""
        self._configs[config.name] = config

        if save:
            self._save_config(config)

    def _save_config(self, config: ModelConfig) -> None:
        """Save a model configuration to file."""
        config_file = self.config_dir / f"{config.name}.json"

        config_data = {
            "name": config.name,
            "type": config.type.value,
            "model_path": config.model_path,
            "context_length": config.context_length,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "quantization": config.quantization,
            "gpu_layers": config.gpu_layers,
            "threads": config.threads,
        }

        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Saved model config: {config_file}")

    def remove_config(self, name: str) -> bool:
        """Remove a model configuration."""
        if name in self._configs:
            del self._configs[name]

            # Remove config file if it exists
            config_file = self.config_dir / f"{name}.json"
            if config_file.exists():
                config_file.unlink()
                logger.info(f"Removed model config file: {config_file}")

            return True
        return False

    def validate_config(self, config: ModelConfig) -> list[str]:
        """Validate a model configuration and return any issues."""
        issues = []

        # Check if model path exists
        model_path = Path(config.model_path)
        if not model_path.exists():
            issues.append(f"Model file does not exist: {config.model_path}")

        # Check context length
        if config.context_length <= 0:
            issues.append("Context length must be positive")
        elif config.context_length > 32768:
            issues.append("Context length seems very large (>32k)")

        # Check temperature
        if not (0.0 <= config.temperature <= 2.0):
            issues.append("Temperature should be between 0.0 and 2.0")

        # Check max tokens
        if config.max_tokens <= 0:
            issues.append("Max tokens must be positive")
        elif config.max_tokens > config.context_length:
            issues.append("Max tokens exceeds context length")

        # Check quantization format
        valid_quants = [
            "Q2_K",
            "Q3_K_S",
            "Q3_K_M",
            "Q3_K_L",
            "Q4_0",
            "Q4_1",
            "Q4_K_S",
            "Q4_K_M",
            "Q5_0",
            "Q5_1",
            "Q5_K_S",
            "Q5_K_M",
            "Q6_K",
            "Q8_0",
            "F16",
            "F32",
        ]
        if config.quantization not in valid_quants:
            issues.append(f"Unknown quantization: {config.quantization}")

        return issues

    def get_recommended_config(
        self,
        memory_limit_gb: float | None = None,
        prefer_speed: bool = False,
        prefer_quality: bool = False,
    ) -> ModelConfig | None:
        """Get a recommended configuration based on constraints."""
        if not self._configs:
            return None

        configs = list(self._configs.values())

        # Filter by memory constraints if specified
        if memory_limit_gb:
            # Rough estimate: Q4_K_M uses ~4 bits per parameter
            # For 8B model with Q4_K_M: ~4GB, Q6_K: ~6GB, Q2_K: ~2GB
            memory_estimates = {
                "Q2_K": 2.0,
                "Q3_K_S": 3.0,
                "Q3_K_M": 3.5,
                "Q3_K_L": 3.8,
                "Q4_0": 4.0,
                "Q4_1": 4.5,
                "Q4_K_S": 4.0,
                "Q4_K_M": 4.5,
                "Q5_0": 5.0,
                "Q5_1": 5.5,
                "Q5_K_S": 5.0,
                "Q5_K_M": 5.5,
                "Q6_K": 6.0,
                "Q8_0": 8.0,
                "F16": 16.0,
                "F32": 32.0,
            }

            filtered_configs = []
            for config in configs:
                estimated_memory = memory_estimates.get(config.quantization, 8.0)
                # Adjust for model size (rough heuristic)
                if "70b" in config.name.lower():
                    estimated_memory *= 8.75  # 70B/8B ratio
                elif "13b" in config.name.lower():
                    estimated_memory *= 1.625  # 13B/8B ratio

                if estimated_memory <= memory_limit_gb:
                    filtered_configs.append(config)

            configs = filtered_configs

        if not configs:
            return None

        # Apply preferences
        if prefer_speed:
            # Prefer smaller quantizations
            configs.sort(key=lambda c: c.quantization)
        elif prefer_quality:
            # Prefer larger quantizations
            quant_order = [
                "Q2_K",
                "Q3_K_S",
                "Q3_K_M",
                "Q3_K_L",
                "Q4_0",
                "Q4_1",
                "Q4_K_S",
                "Q4_K_M",
                "Q5_0",
                "Q5_1",
                "Q5_K_S",
                "Q5_K_M",
                "Q6_K",
                "Q8_0",
                "F16",
                "F32",
            ]
            configs.sort(
                key=lambda c: quant_order.index(c.quantization)
                if c.quantization in quant_order
                else 999,
                reverse=True,
            )

        return configs[0]


# Global config loader instance
_config_loader: ModelConfigLoader | None = None


def get_model_config_loader() -> ModelConfigLoader:
    """Get the global model configuration loader."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ModelConfigLoader()
    return _config_loader


def load_model_config(name: str) -> ModelConfig | None:
    """Load a model configuration by name."""
    return get_model_config_loader().get_config(name)


def list_available_models() -> list[str]:
    """List all available model configurations."""
    return get_model_config_loader().list_configs()
