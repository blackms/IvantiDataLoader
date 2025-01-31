"""Data loading pipeline orchestrator."""
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type

import yaml
from pydantic import BaseModel

from ..core.base import (
    DataLoader,
    DataReader,
    DataSourceConfig,
    DataTransformer,
    LoadResult,
    LoaderConfig
)
from ..core.exceptions import PipelineError
from ..plugins.registry import PluginRegistry
from ..utils.logging import get_logger

logger = get_logger()


class Pipeline:
    """Data loading pipeline orchestrator."""

    def __init__(
        self,
        config_path: Optional[str | Path] = None,
        config: Optional[LoaderConfig] = None
    ):
        """
        Initialize pipeline.

        Args:
            config_path: Path to YAML configuration file
            config: Direct configuration object

        Raises:
            PipelineError: If neither config_path nor config is provided
        """
        if not config_path and not config:
            raise PipelineError(
                "Either config_path or config must be provided"
            )

        if config_path:
            self.config = self._load_config(config_path)
        else:
            self.config = config

        # Initialize components
        self._reader = self._create_reader()
        self._transformer = self._create_transformer()
        self._loader = self._create_loader()
        self._result = LoadResult()

    def _load_config(self, config_path: str | Path) -> LoaderConfig:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            LoaderConfig: Loaded configuration

        Raises:
            PipelineError: If configuration loading fails
        """
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return LoaderConfig(**config_data)

        except Exception as e:
            raise PipelineError(
                f"Failed to load configuration: {str(e)}"
            ) from e

    def _create_reader(self) -> DataReader:
        """
        Create configured reader plugin.

        Returns:
            DataReader: Configured reader instance

        Raises:
            PipelineError: If reader creation fails
        """
        try:
            reader_cls = PluginRegistry.get_reader(self.config.source.type)
            return reader_cls(self.config.source)

        except Exception as e:
            raise PipelineError(
                f"Failed to create reader: {str(e)}"
            ) from e

    def _create_transformer(self) -> DataTransformer:
        """
        Create configured transformer plugin.

        Returns:
            DataTransformer: Configured transformer instance

        Raises:
            PipelineError: If transformer creation fails
        """
        try:
            transformer_cls = PluginRegistry.get_transformer("field_mapper")
            return transformer_cls(self.config.mappings)

        except Exception as e:
            raise PipelineError(
                f"Failed to create transformer: {str(e)}"
            ) from e

    def _create_loader(self) -> DataLoader:
        """
        Create configured loader plugin.

        Returns:
            DataLoader: Configured loader instance

        Raises:
            PipelineError: If loader creation fails
        """
        try:
            loader_cls = PluginRegistry.get_loader("ivanti")
            return loader_cls(self.config.target)

        except Exception as e:
            raise PipelineError(
                f"Failed to create loader: {str(e)}"
            ) from e

    def _process_record(self, record: Dict[str, Any]) -> bool:
        """
        Process a single record through the pipeline.

        Args:
            record: Record to process

        Returns:
            bool: True if successful
        """
        try:
            # Transform record
            transformed_data = self._transformer.transform(record)

            # Load transformed data
            return self._loader.load(transformed_data)

        except Exception as e:
            logger.error(
                "Record processing failed",
                error=str(e),
                record=record
            )
            return False

    def execute(self) -> LoadResult:
        """
        Execute the data loading pipeline.

        Returns:
            LoadResult: Results of the load operation

        Raises:
            PipelineError: If pipeline execution fails
        """
        try:
            logger.info(
                "Starting data load pipeline",
                source_type=self.config.source.type,
                source_name=self.config.source.name
            )

            # Read source data
            records = self._reader.read()
            logger.info(f"Read {len(records)} records from source")

            # Process records
            for record in records:
                try:
                    if self._process_record(record.data):
                        self._result.record_success()
                    else:
                        self._result.record_failure(
                            str(record.row_number),
                            "Processing failed"
                        )

                except Exception as e:
                    self._result.record_failure(
                        str(record.row_number),
                        str(e)
                    )

            # Complete operation
            self._result.complete()
            self._log_results()

            return self._result

        except Exception as e:
            raise PipelineError(
                f"Pipeline execution failed: {str(e)}"
            ) from e

    def _log_results(self) -> None:
        """Log pipeline execution results."""
        logger.info(
            "Pipeline execution completed",
            total_records=self._result.total_records,
            successful=self._result.successful_loads,
            failed=self._result.failed_loads,
            skipped=self._result.skipped_loads,
            duration_seconds=self._result.duration_seconds,
            success_rate=f"{self._result.success_rate:.2f}%"
        )

        if self._result.errors:
            logger.error(
                "Errors occurred during pipeline execution",
                errors=self._result.errors
            )