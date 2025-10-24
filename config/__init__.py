"""
Config package for the Money application.
Contains configuration files and settings.
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

__version__ = "v1.0.6"

__all__ = ['logging', 'logger', '__version__']