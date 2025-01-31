"""Plugin registry for data loader components."""
from typing import Dict, Type, TypeVar

from ..core.base import DataReader, DataTransformer, DataLoader
from ..core.exceptions import PluginError

T = TypeVar('T')
PluginTypes = DataReader | DataTransformer | DataLoader


class PluginRegistry:
    """Registry for data loader plugins."""

    _readers: Dict[str, Type[DataReader]] = {}
    _transformers: Dict[str, Type[DataTransformer]] = {}
    _loaders: Dict[str, Type[DataLoader]] = {}

    @classmethod
    def register_reader(cls, name: str) -> callable:
        """
        Register a reader plugin.

        Args:
            name: Name of the reader plugin

        Returns:
            callable: Decorator function
        """
        def decorator(reader_cls: Type[DataReader]) -> Type[DataReader]:
            if name in cls._readers:
                raise PluginError(f"Reader plugin '{name}' already registered")
            cls._readers[name] = reader_cls
            return reader_cls
        return decorator

    @classmethod
    def register_transformer(cls, name: str) -> callable:
        """
        Register a transformer plugin.

        Args:
            name: Name of the transformer plugin

        Returns:
            callable: Decorator function
        """
        def decorator(transformer_cls: Type[DataTransformer]) -> Type[DataTransformer]:
            if name in cls._transformers:
                raise PluginError(f"Transformer plugin '{name}' already registered")
            cls._transformers[name] = transformer_cls
            return transformer_cls
        return decorator

    @classmethod
    def register_loader(cls, name: str) -> callable:
        """
        Register a loader plugin.

        Args:
            name: Name of the loader plugin

        Returns:
            callable: Decorator function
        """
        def decorator(loader_cls: Type[DataLoader]) -> Type[DataLoader]:
            if name in cls._loaders:
                raise PluginError(f"Loader plugin '{name}' already registered")
            cls._loaders[name] = loader_cls
            return loader_cls
        return decorator

    @classmethod
    def get_reader(cls, name: str) -> Type[DataReader]:
        """
        Get a reader plugin by name.

        Args:
            name: Name of the reader plugin

        Returns:
            Type[DataReader]: Reader plugin class

        Raises:
            PluginError: If plugin not found
        """
        if name not in cls._readers:
            raise PluginError(f"Reader plugin '{name}' not found")
        return cls._readers[name]

    @classmethod
    def get_transformer(cls, name: str) -> Type[DataTransformer]:
        """
        Get a transformer plugin by name.

        Args:
            name: Name of the transformer plugin

        Returns:
            Type[DataTransformer]: Transformer plugin class

        Raises:
            PluginError: If plugin not found
        """
        if name not in cls._transformers:
            raise PluginError(f"Transformer plugin '{name}' not found")
        return cls._transformers[name]

    @classmethod
    def get_loader(cls, name: str) -> Type[DataLoader]:
        """
        Get a loader plugin by name.

        Args:
            name: Name of the loader plugin

        Returns:
            Type[DataLoader]: Loader plugin class

        Raises:
            PluginError: If plugin not found
        """
        if name not in cls._loaders:
            raise PluginError(f"Loader plugin '{name}' not found")
        return cls._loaders[name]

    @classmethod
    def list_plugins(cls) -> Dict[str, Dict[str, Type[PluginTypes]]]:
        """
        List all registered plugins.

        Returns:
            Dict[str, Dict[str, Type[PluginTypes]]]: Dictionary of plugin types and their registered plugins
        """
        return {
            "readers": cls._readers.copy(),
            "transformers": cls._transformers.copy(),
            "loaders": cls._loaders.copy()
        }