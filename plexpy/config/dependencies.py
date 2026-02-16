from typing import Optional, TYPE_CHECKING

_config_instance: Optional['Config'] = None


def set_config(config: 'Config') -> None:
    """Set the global config instance. Called during application bootstrap."""
    global _config_instance
    _config_instance = config


def get_config() -> 'Config':
    """Get the current config instance.
    
    Returns the global config instance. Raises RuntimeError if not initialized.
    Use this in production code where config is guaranteed to be set during bootstrap.
    """
    if _config_instance is None:
        raise RuntimeError(
            "Config not initialized. "
            "Call set_config() during application bootstrap "
            "or use get_config_optional() for testing."
        )
    return _config_instance


def get_config_optional() -> Optional['Config']:
    """Get the current config instance, or None if not initialized.
    
    Use this for testing or optional config access.
    """
    return _config_instance


def clear_config() -> None:
    """Clear the global config instance. Use for testing."""
    global _config_instance
    _config_instance = None


if TYPE_CHECKING:
    from plexpy.config.core import Config
