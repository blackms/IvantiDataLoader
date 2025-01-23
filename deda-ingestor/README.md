# Deda Ingestor

A Python application that processes product data from RabbitMQ and syncs it with Ivanti.

## Features

- Consumes JSON messages from RabbitMQ containing product information
- Validates and transforms product data
- Syncs products with Ivanti through REST API
- Scheduled execution (daily)
- Comprehensive logging and reporting
- Error handling with retry mechanism

## Architecture

The application follows clean architecture principles and implements several design patterns:

- **Dependency Injection**: Loose coupling between components
- **Repository Pattern**: Data access abstraction
- **Adapter Pattern**: Data transformation
- **Factory Pattern**: Object creation

### Project Structure

```
src/
├── deda_ingestor/
│   ├── adapters/           # Data transformation adapters
│   │   ├── __init__.py
│   │   └── product_adapter.py
│   ├── config/            # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/             # Core business logic
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── product_service.py
│   ├── factories/        # Factory classes
│   │   ├── __init__.py
│   │   └── connection_factory.py
│   ├── repositories/     # Data access layer
│   │   ├── __init__.py
│   │   ├── rabbitmq_repository.py
│   │   └── ivanti_repository.py
│   ├── scheduler/        # Scheduling logic
│   │   ├── __init__.py
│   │   └── job_scheduler.py
│   └── utils/           # Utility functions
│       ├── __init__.py
│       └── logging_config.py
└── main.py             # Application entry point
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
poetry install
```

## Configuration

Create a `.env` file in the project root:

```env
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=products_queue

# Ivanti API Configuration
IVANTI_API_URL=https://ivanti-api.example.com
IVANTI_API_KEY=your_api_key
IVANTI_CLIENT_ID=your_client_id
IVANTI_CLIENT_SECRET=your_client_secret

# Application Configuration
LOG_LEVEL=INFO
SCHEDULE_TIME=02:00  # 24-hour format
MAX_RETRIES=3
RETRY_DELAY=5  # seconds
```

## Usage

Run the application:

```bash
poetry run python -m deda_ingestor
```

### Message Format

Expected JSON message format:

```json
{
    "productId": "123",
    "productName": "Example Product",
    "version": "1.0.0",
    "attributes": {
        "category": "Software",
        "manufacturer": "Example Corp",
        "releaseDate": "2024-01-23"
    }
}
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
poetry run black .
poetry run isort .
poetry run flake8
```

## Logging

Logs are stored in the `logs` directory:
- `app.log`: General application logs
- `error.log`: Error-specific logs
- `sync_report.log`: Daily synchronization reports

## License

MIT