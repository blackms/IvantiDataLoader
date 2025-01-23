# 🚀 Deda Ingestor

> 🔄 A robust Python application that synchronizes product data between RabbitMQ and Ivanti

## 🌟 Features

- 📦 Consumes JSON messages from RabbitMQ containing product information
- ✨ Smart data validation and transformation
- 🔄 Bidirectional sync with Ivanti through REST API
- ⏰ Configurable scheduled execution
- 📊 Comprehensive logging and reporting
- 🔁 Intelligent retry mechanisms with exponential backoff
- 🛡️ Robust error handling and recovery

## 🏗️ Architecture

The application follows clean architecture principles and implements several design patterns:

### 🎯 Design Patterns

- 💉 **Dependency Injection**: Loose coupling between components
- 📚 **Repository Pattern**: Clean data access abstraction
- 🔄 **Adapter Pattern**: Smart data transformation
- 🏭 **Factory Pattern**: Flexible object creation

### 📁 Project Structure

```
src/
├── deda_ingestor/
│   ├── adapters/           # 🔄 Data transformation
│   │   ├── __init__.py
│   │   ├── base.py        # 🎯 Base adapter interfaces
│   │   └── product_adapter.py
│   ├── config/            # ⚙️ Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/             # 💼 Core business logic
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   └── product_service.py
│   ├── repositories/     # 📦 Data access layer
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── rabbitmq_repository.py
│   │   └── ivanti_repository.py
│   ├── scheduler/        # ⏰ Scheduling logic
│   │   ├── __init__.py
│   │   └── job_scheduler.py
│   ├── utils/           # 🛠️ Utility functions
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── retry.py
│   ├── __init__.py
│   ├── __main__.py      # 🎮 Entry point
│   └── container.py     # 💉 Dependency injection
└── tests/              # 🧪 Test suite
```

## 🚀 Getting Started

### 📋 Prerequisites

- 🐍 Python 3.9 or higher
- 🐰 RabbitMQ server
- 🔑 Ivanti API credentials

### 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/deda-ingestor.git
cd deda-ingestor
```

2. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install
```

### ⚙️ Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```env
# 🐰 RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=products_queue

# 🔑 Ivanti API Configuration
IVANTI_API_URL=https://ivanti-api.example.com
IVANTI_API_KEY=your_api_key
IVANTI_CLIENT_ID=your_client_id
IVANTI_CLIENT_SECRET=your_client_secret

# 📝 Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs

# ⏰ Scheduler Configuration
SCHEDULE_TIME=02:00
TIMEZONE=UTC
```

## 🎮 Usage

### 🔄 Running the Application

#### Scheduled Execution
```bash
poetry run python -m deda_ingestor
```

#### Immediate Execution
```bash
poetry run python -m deda_ingestor --run-now
```

#### Custom Log Level
```bash
poetry run python -m deda_ingestor --log-level DEBUG
```

### 📊 Message Format

Expected JSON message format:
```json
{
  "productId": "P12345",
  "productName": "Example Product",
  "productElements": [
    {
      "Lenght": 50,
      "Procuct Element": "Element 1",
      "Type": "Hardware",
      "GG Startup": 3,
      "RU": "Resource Unit",
      "RU Qty": 10,
      "RU Unit of measure": "Days",
      "Q.ty min": 1,
      "Q.ty MAX": 100,
      "%Sconto MAX": 15,
      "Startup Costo": 500.0,
      "Startup Margine": 20,
      "Startup Prezzo": 600.0,
      "Canone Costo Mese": 100.0,
      "Canone Margine": 10,
      "Canone Prezzo Mese": 110.0,
      "Extended Description": "Detailed description",
      "Profit Center Prevalente": "PC001",
      "Status": "Active"
    }
  ]
}
```

## 📊 Logging

The application uses structured logging with different outputs:

- 📝 `app.log`: General application logs
- ❌ `error.log`: Error-specific logs
- 📊 `sync_report.log`: Daily synchronization reports

Log files are automatically rotated and compressed.

## 🧪 Development

### Running Tests
```bash
# 🧪 Run all tests
poetry run pytest

# 🔍 Run with coverage
poetry run pytest --cov

# 🚀 Run in parallel
poetry run pytest -n auto
```

### 🧹 Code Quality
```bash
# 🎨 Format code
poetry run black .
poetry run isort .

# 🔍 Lint code
poetry run flake8
poetry run mypy .

# 🛡️ Security checks
poetry run bandit -r src/
poetry run safety check
```

### 🏗️ Pre-commit Hooks

Install pre-commit hooks:
```bash
poetry run pre-commit install
```

## 🔒 Error Handling

The application implements a comprehensive error handling strategy:

- 🔁 Automatic retries for transient failures
- 📊 Detailed error logging and tracking
- 🔄 Dead Letter Queue (DLQ) for failed messages
- 🛡️ Circuit breaker for external services

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create your feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🎁 Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- 🐰 RabbitMQ team for the amazing message broker
- 🔧 Ivanti team for their API
- 🐍 Python community for the awesome ecosystem

## 📞 Support

For support and questions:
- 📧 Email: support@example.com
- 💬 Issues: GitHub Issues
- 📚 Wiki: Project Wiki

---
Made with ❤️ by Your Team