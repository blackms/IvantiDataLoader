"""Tests for the ProductAdapter class."""
from datetime import datetime
import pytest

from deda_ingestor.adapters.product_adapter import ProductAdapter
from deda_ingestor.core.models import Product, ProductAttributes, IvantiProduct


@pytest.fixture
def sample_rabbitmq_message():
    """Sample RabbitMQ message fixture."""
    return {
        "productId": "PROD-123",
        "productName": "Test Product",
        "version": "1.0.0",
        "attributes": {
            "category": "Software",
            "manufacturer": "Test Corp",
            "releaseDate": "2024-01-23T12:00:00Z",
            "description": "Test product description",
            "platform": "Windows",
            "language": "EN",
            "licenseType": "Perpetual",
            "customField1": "Custom Value 1",
            "customField2": "Custom Value 2"
        }
    }


@pytest.fixture
def sample_ivanti_response():
    """Sample Ivanti API response fixture."""
    return {
        "id": "PROD-123",
        "name": "Test Product",
        "category": "Software",
        "manufacturer": "Test Corp",
        "releaseDate": "2024-01-23T12:00:00Z",
        "description": "Test product description",
        "version": "1.0.0",
        "status": "active",
        "createdAt": "2024-01-23T12:00:00Z",
        "updatedAt": "2024-01-23T12:00:00Z",
        "customFields": {
            "platform": "Windows",
            "language": "EN",
            "license_type": "Perpetual",
            "customField1": "Custom Value 1",
            "customField2": "Custom Value 2"
        }
    }


def test_from_rabbitmq_message(sample_rabbitmq_message):
    """Test conversion from RabbitMQ message to Product."""
    # When
    product = ProductAdapter.from_rabbitmq_message(sample_rabbitmq_message)

    # Then
    assert isinstance(product, Product)
    assert product.product_id == "PROD-123"
    assert product.product_name == "Test Product"
    assert isinstance(product.attributes, ProductAttributes)
    assert product.attributes.category == "Software"
    assert product.attributes.manufacturer == "Test Corp"
    assert product.attributes.version == "1.0.0"
    assert product.attributes.platform == "Windows"
    assert product.attributes.language == "EN"
    assert product.attributes.license_type == "Perpetual"
    assert product.attributes.additional_info == {
        "customField1": "Custom Value 1",
        "customField2": "Custom Value 2"
    }


def test_to_ivanti_product():
    """Test conversion from Product to IvantiProduct."""
    # Given
    product = Product(
        product_id="PROD-123",
        product_name="Test Product",
        attributes=ProductAttributes(
            category="Software",
            manufacturer="Test Corp",
            release_date=datetime(2024, 1, 23, 12, 0),
            description="Test product description",
            version="1.0.0",
            platform="Windows",
            language="EN",
            license_type="Perpetual",
            additional_info={
                "customField1": "Custom Value 1",
                "customField2": "Custom Value 2"
            }
        )
    )

    # When
    ivanti_product = ProductAdapter.to_ivanti_product(product)

    # Then
    assert isinstance(ivanti_product, IvantiProduct)
    assert ivanti_product.id == "PROD-123"
    assert ivanti_product.name == "Test Product"
    assert ivanti_product.category == "Software"
    assert ivanti_product.manufacturer == "Test Corp"
    assert ivanti_product.version == "1.0.0"
    assert ivanti_product.custom_fields == {
        "platform": "Windows",
        "language": "EN",
        "license_type": "Perpetual",
        "customField1": "Custom Value 1",
        "customField2": "Custom Value 2"
    }


def test_from_ivanti_response(sample_ivanti_response):
    """Test conversion from Ivanti response to Product."""
    # When
    product = ProductAdapter.from_ivanti_response(sample_ivanti_response)

    # Then
    assert isinstance(product, Product)
    assert product.product_id == "PROD-123"
    assert product.product_name == "Test Product"
    assert product.attributes.category == "Software"
    assert product.attributes.manufacturer == "Test Corp"
    assert product.attributes.version == "1.0.0"
    assert product.attributes.platform == "Windows"
    assert product.attributes.language == "EN"
    assert product.attributes.license_type == "Perpetual"
    assert product.attributes.additional_info == {
        "customField1": "Custom Value 1",
        "customField2": "Custom Value 2"
    }


def test_from_rabbitmq_message_missing_required_fields():
    """Test handling of missing required fields in RabbitMQ message."""
    # Given
    invalid_message = {
        "attributes": {
            "category": "Software"
        }
    }

    # When/Then
    with pytest.raises(ValueError):
        ProductAdapter.from_rabbitmq_message(invalid_message)


def test_from_rabbitmq_message_invalid_date():
    """Test handling of invalid release date in RabbitMQ message."""
    # Given
    message_with_invalid_date = {
        "productId": "PROD-123",
        "productName": "Test Product",
        "attributes": {
            "releaseDate": "invalid-date"
        }
    }

    # When
    product = ProductAdapter.from_rabbitmq_message(message_with_invalid_date)

    # Then
    assert product.attributes.release_date is None