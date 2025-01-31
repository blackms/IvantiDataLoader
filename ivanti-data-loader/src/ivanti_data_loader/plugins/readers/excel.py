"""Excel file reader plugin."""
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from pydantic import BaseModel, Field

from ...core.base import DataReader, DataSourceConfig
from ...core.exceptions import ReaderError
from ..registry import PluginRegistry


class ExcelReaderConfig(DataSourceConfig):
    """Configuration for Excel reader."""
    type: str = "excel"
    file_path: str = Field(..., description="Path to Excel file")
    sheet_name: str = Field(
        default="Sheet1",
        description="Name of the sheet to read"
    )
    header_row: int = Field(
        default=0,
        description="Row number containing column headers (0-based)"
    )
    skip_rows: int = Field(
        default=0,
        description="Number of rows to skip before header"
    )
    required_columns: List[str] = Field(
        default_factory=list,
        description="List of required column names"
    )


class ExcelRecord(BaseModel):
    """Model for Excel record data."""
    row_number: int
    data: Dict[str, Any]


@PluginRegistry.register_reader("excel")
class ExcelReader(DataReader[ExcelRecord]):
    """Reader plugin for Excel files."""

    def __init__(self, config: ExcelReaderConfig):
        """
        Initialize Excel reader.

        Args:
            config: Reader configuration
        """
        super().__init__(config)
        self.file_path = Path(config.file_path)
        if not self.file_path.exists():
            raise ReaderError(f"Excel file not found: {self.file_path}")

    def read(self) -> List[ExcelRecord]:
        """
        Read data from Excel file.

        Returns:
            List[ExcelRecord]: List of records from Excel

        Raises:
            ReaderError: If reading fails
        """
        try:
            # Read Excel file
            df = pd.read_excel(
                self.file_path,
                sheet_name=self.config.sheet_name,
                header=self.config.header_row,
                skiprows=self.config.skip_rows
            )

            # Validate required columns
            if self.config.required_columns:
                missing_columns = set(self.config.required_columns) - set(df.columns)
                if missing_columns:
                    raise ReaderError(
                        f"Required columns missing: {', '.join(missing_columns)}"
                    )

            # Convert to records
            records = []
            for index, row in df.iterrows():
                # Convert row to dictionary, handling NaN values
                data = {}
                for column in df.columns:
                    value = row[column]
                    # Convert NaN/None to None for consistency
                    data[column] = None if pd.isna(value) else value

                record = ExcelRecord(
                    row_number=index + self.config.header_row + self.config.skip_rows + 2,
                    data=data
                )
                
                if self.validate(record):
                    records.append(record)

            return records

        except Exception as e:
            if isinstance(e, ReaderError):
                raise
            raise ReaderError(f"Failed to read Excel file: {str(e)}") from e

    def validate(self, record: ExcelRecord) -> bool:
        """
        Validate Excel record.

        Args:
            record: Record to validate

        Returns:
            bool: True if valid
        """
        try:
            # Check for required columns
            if self.config.required_columns:
                for column in self.config.required_columns:
                    if column not in record.data or record.data[column] is None:
                        return False
            return True

        except Exception as e:
            raise ReaderError(
                f"Failed to validate record at row {record.row_number}: {str(e)}"
            ) from e