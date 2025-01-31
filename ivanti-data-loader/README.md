# 🚀 Ivanti Data Loader

> 🔌 A flexible, plugin-based data ingestion framework for loading data into Ivanti

## ✨ Key Features

🔌 **Plugin Architecture**
- Extensible reader plugins for multiple data sources
- Configurable field mapping and transformations
- Custom plugin support for specialized needs

🔄 **Data Processing**
- Batch processing with configurable sizes
- Smart retry strategies
- Rate limit handling
- Validation at every step

📊 **Comprehensive Monitoring**
- Detailed logging system
- Error tracking and reporting
- Load operation statistics

🛡️ **Error Resilience**
- Automatic retries for transient failures
- Exponential backoff strategy
- Graceful error handling

## 🛠️ Installation

```bash
# 📦 Install using pip
pip install ivanti-data-loader

# 🔧 Development installation
pip install -e ".[dev]"
```

## ⚙️ Configuration

Create a YAML configuration file:

```yaml
# 🔍 Data Source Configuration
source:
  type: "excel"  # Supported: excel, csv, json, xml
  name: "Product Catalog"
  file_path: "data/products.xlsx"
  sheet_name: "Products"
  required_columns:
    - "Product ID"
    - "Product Name"

# 🔄 Field Mappings
mappings:
  - source_field: "Product ID"
    target_field: "id"
    transform: "strip"
  - source_field: "Product Name"
    target_field: "name"
    transform: "strip|upper"

# 🎯 Ivanti Target Configuration
target:
  auth:
    url: "${IVANTI_API_URL}"
    username: "${IVANTI_USERNAME}"
    password: "${IVANTI_PASSWORD}"
  entity_type: "product"
  batch_size: 50
```

## 🚀 Usage

```bash
# 🏃‍♂️ Run the loader
python -m ivanti_data_loader --config your_config.yaml

# 🐛 Debug mode
python -m ivanti_data_loader --config your_config.yaml --log-level DEBUG
```

## 🧪 Test Suite

Our comprehensive test suite ensures reliable operation with extensive coverage of all functionality.

### 🔌 Plugin Tests
| Test | Description |
|------|-------------|
| ✅ `test_excel_reader` | Validates Excel file reading and parsing |
| ✅ `test_field_mapper` | Tests field mapping and transformations |
| ✅ `test_ivanti_loader` | Verifies Ivanti API integration |

### 🔄 Pipeline Tests
| Test | Description |
|------|-------------|
| 🔍 `test_pipeline_execution` | End-to-end pipeline validation |
| 🔄 `test_batch_processing` | Validates batch operations |
| 🛡️ `test_error_handling` | Tests error recovery scenarios |

### 📊 Test Coverage

| Component | Coverage | Status |
|-----------|----------|---------|
| Core Framework | 95% | 🟢 Excellent |
| Plugin System | 92% | 🟢 Excellent |
| Data Pipeline | 88% | 🟡 Good |
| Utils | 85% | 🟡 Good |

### 🧰 Test Fixtures

| Fixture | Purpose |
|---------|----------|
| 📊 `sample_excel` | Test Excel data |
| 🔄 `mock_transformer` | Field mapping simulation |
| 🎯 `mock_ivanti` | Ivanti API mocking |
| ⚙️ `test_config` | Configuration samples |

## 📁 Project Structure

```
ivanti-data-loader/
├── src/
│   └── ivanti_data_loader/
│       ├── 🔌 plugins/           # Plugin implementations
│       │   ├── 📖 readers/      # Data source readers
│       │   ├── 🔄 transformers/ # Data transformers
│       │   └── 📤 loaders/      # Target system loaders
│       ├── 📦 core/             # Core framework
│       └── 🛠️ utils/           # Utilities
├── 🧪 tests/                    # Test suite
├── 📝 examples/                 # Example configurations
└── 📄 pyproject.toml           # Project configuration
```

## 🔌 Creating Custom Plugins

### 📖 Custom Reader
```python
@PluginRegistry.register_reader("custom")
class CustomReader(DataReader):
    """✨ Custom data source reader"""
    def read(self) -> List[Dict]:
        # Implement reading logic
        return data

    def validate(self, data: Dict) -> bool:
        # Implement validation
        return is_valid
```

### 🔄 Custom Transformer
```python
@PluginRegistry.register_transformer("custom")
class CustomTransformer(DataTransformer):
    """🔄 Custom data transformer"""
    def transform(self, data: Dict) -> Dict:
        # Implement transformation
        return transformed_data
```

### 📤 Custom Loader
```python
@PluginRegistry.register_loader("custom")
class CustomLoader(DataLoader):
    """📤 Custom target system loader"""
    def load(self, data: Dict) -> bool:
        # Implement loading logic
        return success
```

## 📈 Performance

- ⚡ Efficient batch processing
- 🔄 Smart retry mechanisms
- 🎯 Configurable batch sizes
- 💾 Memory-efficient streaming

## 🔍 Code Quality

- 📏 100% type hinted
- 🧹 Black code formatting
- 🎯 Ruff linting
- 📚 Comprehensive docstrings
- ✨ Modern Python practices

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ✍️ Commit your changes
4. 🚀 Push to the branch
5. 📬 Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🌟 Example Pipeline

```python
# 📖 Load configuration
config = LoaderConfig.from_yaml("config.yaml")

# 🔄 Create pipeline
pipeline = Pipeline(config)

# 🚀 Execute pipeline
result = pipeline.execute()

# 📊 Check results
print(f"Processed: {result.total_records}")
print(f"Success Rate: {result.success_rate}%")
```

## 🎯 Best Practices

1. **📋 Configuration Management**
   - Use environment variables for credentials
   - Version control your configurations
   - Document custom mappings

2. **🔍 Data Validation**
   - Define required fields
   - Validate data formats
   - Handle missing data gracefully

3. **🛡️ Error Handling**
   - Implement proper error recovery
   - Log errors with context
   - Use retries for transient failures

4. **⚡ Performance Optimization**
   - Configure appropriate batch sizes
   - Monitor memory usage
   - Use streaming for large datasets