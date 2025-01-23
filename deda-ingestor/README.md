# 🚀 Deda Ingestor

> 🔄 Seamlessly sync product data from RabbitMQ to Ivanti

## ✨ Key Features

🔐 **Secure Authentication**
- OAuth2 authentication with Ivanti API
- Automatic token refresh
- Secure credential handling

🔄 **Robust Data Sync**
- Batch processing of product data
- Smart retry strategies
- Rate limit handling

📊 **Comprehensive Monitoring**
- Detailed logging system
- Error tracking and reporting
- Sync status monitoring

🛡️ **Error Resilience**
- Automatic retries for transient failures
- Exponential backoff strategy
- Rate limit respect

## 🛠️ Installation

```bash
# 📦 Install dependencies using Poetry
poetry install
```

## ⚙️ Configuration

Create a `.env` file based on `.env.example`:

```env
# 🔑 Ivanti API Configuration
IVANTI_API_URL=https://ivanti-api.example.com
IVANTI_API_KEY=your-api-key
IVANTI_CLIENT_ID=your-client-id
IVANTI_CLIENT_SECRET=your-client-secret
IVANTI_TOKEN_URL=https://ivanti-api.example.com/oauth/token

# 🐰 RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=products_queue

# 🎛️ Application Settings
LOG_LEVEL=INFO
LOG_DIR=logs
```

## 🚀 Usage

```bash
# 🏃‍♂️ Run the application
poetry run python -m deda_ingestor

# 🧪 Run tests
poetry run pytest
```

## 🧪 Test Suite

Our comprehensive test suite ensures reliable operation with extensive coverage of all functionality.

### 🔐 Authentication Tests
| Test | Description |
|------|-------------|
| ✅ `test_authentication_success` | Validates OAuth2 flow and token handling |
| ❌ `test_authentication_failure` | Verifies proper error handling for auth failures |

### 📦 Product Operations Tests
| Test | Description |
|------|-------------|
| 🔍 `test_get_product_success` | Ensures accurate product retrieval |
| 🚫 `test_get_product_not_found` | Validates 404 handling |
| ➕ `test_create_product_success` | Tests product creation flow |
| 🔄 `test_update_product_success` | Verifies update operations |

### 🛡️ Error Handling Tests
| Test | Description |
|------|-------------|
| 🔄 `test_retry_on_temporary_error` | Validates retry mechanism (503 errors) |
| ⏳ `test_rate_limit_handling` | Tests rate limit handling (429 responses) |

### 📦 Batch Processing Tests
| Test | Description |
|------|-------------|
| 🔄 `test_batch_process_products` | Validates batch operations with mixed results |

### 📊 Test Coverage

| Component | Coverage | Status |
|-----------|----------|---------|
| Base Repository | 100% | 🟢 Perfect |
| Core Models | 94% | 🟢 Excellent |
| Ivanti Repository | 85% | 🟡 Good |
| Utils | 64% | 🟡 Adequate |

### 🧰 Test Fixtures

| Fixture | Purpose |
|---------|----------|
| 🔑 `mock_auth_response` | OAuth2 token simulation |
| ✅ `mock_auth_success` | Successful auth responses |
| ⚙️ `ivanti_config` | Repository configuration |
| 🌐 `mock_httpx_client` | HTTP client mocking |
| 📦 `sample_product` | Test product data |
| 📄 `mock_product_response` | API response simulation |

## 📁 Project Structure

```
deda-ingestor/
├── src/
│   └── deda_ingestor/
│       ├── 🔄 adapters/          # Data transformation
│       ├── ⚙️ config/            # Configuration
│       ├── 📦 core/              # Domain models
│       ├── 💾 repositories/      # Data access
│       ├── ⏰ scheduler/         # Job scheduling
│       └── 🛠️ utils/            # Utilities
├── 🧪 tests/                     # Test suite
├── 📝 poetry.lock               # Dependencies
└── ⚙️ pyproject.toml           # Project config
```

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ✍️ Commit your changes
4. 🚀 Push to the branch
5. 📬 Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🌟 Test Highlights

### Authentication Flow
```python
def test_authentication_success():
    """✅ Validates OAuth2 authentication flow"""
    # Setup token response
    mock_response.json.return_value = {
        "access_token": "test-token",
        "expires_in": 3600
    }
    
    # Execute auth flow
    repository.connect()
    
    # Verify token storage
    assert repository._access_token == "test-token"
```

### Error Handling
```python
def test_retry_on_temporary_error():
    """🔄 Tests retry mechanism for 503 errors"""
    # Setup: 2 failures, then success
    mock_client.put.side_effect = [
        error_503_response,
        error_503_response,
        success_response
    ]
    
    # Should succeed after retries
    success = repository.update_product(product)
    assert success is True
    assert mock_client.put.call_count == 3
```

### Rate Limiting
```python
def test_rate_limit_handling():
    """⏳ Validates rate limit handling"""
    # Setup 429 response
    rate_limit_response.headers = {
        "Retry-After": "2"
    }
    
    # Should handle rate limit and retry
    success = repository.create_product(product)
    assert success is True
```

## 📈 Performance

- ⚡ Fast batch processing
- 🔄 Efficient retry mechanisms
- 🎯 Smart rate limit handling
- 💾 Optimized data transformations

## 🔍 Code Quality

- 📏 100% type hinted
- 🧹 Follows PEP 8
- 📚 Comprehensive docstrings
- ✨ Modern Python practices