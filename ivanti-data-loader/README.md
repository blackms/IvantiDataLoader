# Ivanti Data Loader

A flexible, plugin-based data ingestion framework for loading data into Ivanti from various sources.

## Features

- Plugin-based architecture for easy extensibility
- Support for multiple data sources (Excel, CSV, etc.)
- Configurable field mappings and transformations
- Robust error handling and logging
- Batch processing with retry capabilities
- Environment variable support for sensitive configuration

## Installation

```bash
pip install ivanti-data-loader
```

## Quick Start

1. Create a YAML configuration file (see examples/product_loader_config.yaml)
2. Set required environment variables:
```bash
export IVANTI_USERNAME=your_username
export IVANTI_PASSWORD=your_password
```
3. Run the loader:
```bash
python -m ivanti_data_loader --config your_config.yaml
```

## Configuration

The framework uses YAML configuration files to define:
- Data source settings
- Field mappings and transformations
- Target system configuration

Example configuration:
```yaml
source:
  type: "excel"
  name: "Product Catalog"
  file_path: "data/product_catalog.xlsx"
  sheet_name: "Products"
  
mappings:
  - source_field: "Product ID"
    target_field: "id"
    transform: "strip"

target:
  auth:
    url: "https://ivanti.example.com/api/v1"
    username: "${IVANTI_USERNAME}"
    password: "${IVANTI_PASSWORD}"
```

## Built-in Plugins

### Readers
- Excel Reader: Read data from Excel files
  - Supports multiple sheets
  - Column validation
  - Row filtering

### Transformers
- Field Mapper: Map and transform fields
  - Built-in transformations (string, int, float, bool)
  - Custom transformation support
  - Multiple transformations per field

### Loaders
- Ivanti Loader: Load data into Ivanti
  - Authentication handling
  - Batch processing
  - Automatic retries

## Creating Custom Plugins

### Custom Reader Example
```python
from ivanti_data_loader.core.base import DataReader
from ivanti_data_loader.plugins.registry import PluginRegistry

@PluginRegistry.register_reader("custom")
class CustomReader(DataReader):
    def read(self):
        # Implement reading logic
        pass

    def validate(self, data):
        # Implement validation logic
        pass
```

### Custom Transformer Example
```python
from ivanti_data_loader.core.base import DataTransformer
from ivanti_data_loader.plugins.registry import PluginRegistry

@PluginRegistry.register_transformer("custom")
class CustomTransformer(DataTransformer):
    def transform(self, data):
        # Implement transformation logic
        pass
```

### Custom Loader Example
```python
from ivanti_data_loader.core.base import DataLoader
from ivanti_data_loader.plugins.registry import PluginRegistry

@PluginRegistry.register_loader("custom")
class CustomLoader(DataLoader):
    def load(self, data):
        # Implement loading logic
        pass
```

## Error Handling

The framework provides detailed error handling:
- Validation errors for invalid data
- Connection errors for network issues
- Transformation errors for mapping problems
- Loading errors for target system issues

Errors are logged with context for debugging:
```python
try:
    pipeline.execute()
except DataLoaderError as e:
    logger.error(f"Error: {e.message}", details=e.details)
```

## Logging

Comprehensive logging is provided:
- Operation progress and status
- Error details and context
- Performance metrics
- Success/failure statistics

Configure log level:
```bash
python -m ivanti_data_loader --config config.yaml --log-level DEBUG
```

## Best Practices

1. **Configuration Management**
   - Use environment variables for sensitive data
   - Version control your configurations
   - Document custom mappings

2. **Data Validation**
   - Define required fields
   - Validate data formats
   - Handle missing or invalid data

3. **Error Handling**
   - Implement proper error recovery
   - Log errors with context
   - Use retries for transient failures

4. **Performance**
   - Use batch processing for large datasets
   - Monitor memory usage
   - Implement pagination if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details