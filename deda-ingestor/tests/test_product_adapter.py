"""Tests for the ProductAdapter class."""
from datetime import datetime
from decimal import Decimal
import pytest

from deda_ingestor.adapters.product_adapter import ProductAdapter
from deda_ingestor.core.models import Product, ProductElement, IvantiProduct


@pytest.fixture
def sample_rabbitmq_message():
    """Sample RabbitMQ message fixture."""
    return {
        "productId": "P12345",
        "productName": "Nome di esempio del prodotto",
        "productElements": [
            {
                "Lenght": 50,
                "Procuct Element": "Elemento Prodotto 1",
                "Type": "Hardware",
                "GG Startup": 3,
                "RU": "Resource Unit Esempio",
                "RU Qty": 10,
                "RU Unit of measure": "Giorni",
                "Q.ty min": 1,
                "Q.ty MAX": 100,
                "%Sconto MAX": 15,
                "Startup Costo": 500.0,
                "Startup Margine": 20,
                "Startup Prezzo": 600.0,
                "Canone Costo Mese": 100.0,
                "Canone Margine": 10,
                "Canone Prezzo Mese": 110.0,
                "Extended Description": "Descrizione estesa dell'elemento",
                "Profit Center Prevalente": "Codice Centro di Profitto",
                "Status": "Active",
                "Note": "Eventuali note extra",
                "Object": "Riferimento oggetto"
            },
            {
                "Lenght": 75,
                "Procuct Element": "Elemento Prodotto 2",
                "Type": "Software",
                "GG Startup": 5,
                "RU": "Altro Resource Unit",
                "RU Qty": 20,
                "RU Unit of measure": "Unità",
                "Q.ty min": 1,
                "Q.ty MAX": 50,
                "%Sconto MAX": 10,
                "Startup Costo": 750.0,
                "Startup Margine": 15,
                "Startup Prezzo": 862.5,
                "Canone Costo Mese": 200.0,
                "Canone Margine": 20,
                "Canone Prezzo Mese": 240.0,
                "Extended Description": "Ulteriore descrizione estesa",
                "Profit Center Prevalente": "Altro Centro di Profitto",
                "Status": "Active",
                "Note": "Note su questo elemento",
                "Object": "ID o riferimento specifico"
            }
        ]
    }


@pytest.fixture
def sample_ivanti_response():
    """Sample Ivanti API response fixture."""
    return {
        "id": "P12345",
        "name": "Nome di esempio del prodotto",
        "elements": [
            {
                "id": "elem-001",
                "name": "Elemento Prodotto 1",
                "type": "Hardware",
                "startup_days": 3,
                "resource_unit": "Resource Unit Esempio",
                "resource_unit_qty": 10,
                "resource_unit_measure": "Giorni",
                "quantity_min": 1,
                "quantity_max": 100,
                "max_discount_percentage": 15.0,
                "startup_cost": 500.0,
                "startup_margin": 20.0,
                "startup_price": 600.0,
                "monthly_fee_cost": 100.0,
                "monthly_fee_margin": 10.0,
                "monthly_fee_price": 110.0,
                "extended_description": "Descrizione estesa dell'elemento",
                "profit_center": "Codice Centro di Profitto",
                "status": "Active",
                "notes": "Eventuali note extra",
                "object_reference": "Riferimento oggetto"
            }
        ],
        "status": "Active",
        "created_at": "2024-01-23T12:00:00Z",
        "updated_at": "2024-01-23T12:00:00Z"
    }


def test_from_rabbitmq_message(sample_rabbitmq_message):
    """Test conversion from RabbitMQ message to Product."""
    # When
    product = ProductAdapter.from_rabbitmq_message(sample_rabbitmq_message)

    # Then
    assert isinstance(product, Product)
    assert product.product_id == "P12345"
    assert product.product_name == "Nome di esempio del prodotto"
    assert len(product.product_elements) == 2

    # Verify first element
    element = product.product_elements[0]
    assert isinstance(element, ProductElement)
    assert element.length == 50
    assert element.product_element == "Elemento Prodotto 1"
    assert element.type == "Hardware"
    assert element.startup_days == 3
    assert element.resource_unit == "Resource Unit Esempio"
    assert element.resource_unit_qty == 10
    assert element.resource_unit_measure == "Giorni"
    assert element.quantity_min == 1
    assert element.quantity_max == 100
    assert element.max_discount_percentage == Decimal("15")
    assert element.startup_cost == Decimal("500.0")
    assert element.startup_margin == Decimal("20")
    assert element.startup_price == Decimal("600.0")
    assert element.monthly_fee_cost == Decimal("100.0")
    assert element.monthly_fee_margin == Decimal("10")
    assert element.monthly_fee_price == Decimal("110.0")


def test_to_ivanti_product():
    """Test conversion from Product to IvantiProduct."""
    # Given
    element = ProductElement(
        Lenght=50,
        **{
            "Procuct Element": "Elemento Prodotto 1",
            "Type": "Hardware",
            "GG Startup": 3,
            "RU": "Resource Unit Esempio",
            "RU Qty": 10,
            "RU Unit of measure": "Giorni",
            "Q.ty min": 1,
            "Q.ty MAX": 100,
            "%Sconto MAX": Decimal("15"),
            "Startup Costo": Decimal("500.0"),
            "Startup Margine": Decimal("20"),
            "Startup Prezzo": Decimal("600.0"),
            "Canone Costo Mese": Decimal("100.0"),
            "Canone Margine": Decimal("10"),
            "Canone Prezzo Mese": Decimal("110.0"),
            "Extended Description": "Descrizione estesa dell'elemento",
            "Profit Center Prevalente": "Codice Centro di Profitto",
            "Status": "Active",
            "Note": "Eventuali note extra",
            "Object": "Riferimento oggetto"
        }
    )

    product = Product(
        product_id="P12345",
        product_name="Nome di esempio del prodotto",
        product_elements=[element]
    )

    # When
    ivanti_product = ProductAdapter.to_ivanti_product(product)

    # Then
    assert isinstance(ivanti_product, IvantiProduct)
    assert ivanti_product.id == "P12345"
    assert ivanti_product.name == "Nome di esempio del prodotto"
    assert len(ivanti_product.elements) == 1

    ivanti_element = ivanti_product.elements[0]
    assert ivanti_element.name == "Elemento Prodotto 1"
    assert ivanti_element.type == "Hardware"
    assert ivanti_element.startup_days == 3
    assert ivanti_element.resource_unit == "Resource Unit Esempio"
    assert ivanti_element.max_discount_percentage == 15.0
    assert ivanti_element.startup_cost == 500.0
    assert ivanti_element.monthly_fee_price == 110.0


def test_from_ivanti_response(sample_ivanti_response):
    """Test conversion from Ivanti response to Product."""
    # When
    product = ProductAdapter.from_ivanti_response(sample_ivanti_response)

    # Then
    assert isinstance(product, Product)
    assert product.product_id == "P12345"
    assert product.product_name == "Nome di esempio del prodotto"
    assert len(product.product_elements) == 1

    element = product.product_elements[0]
    assert element.product_element == "Elemento Prodotto 1"
    assert element.type == "Hardware"
    assert element.startup_days == 3
    assert element.max_discount_percentage == Decimal("15.0")
    assert element.startup_cost == Decimal("500.0")
    assert element.monthly_fee_price == Decimal("110.0")


def test_from_rabbitmq_message_missing_required_fields():
    """Test handling of missing required fields in RabbitMQ message."""
    # Given
    invalid_message = {
        "productElements": [
            {
                "Type": "Hardware"
            }
        ]
    }

    # When/Then
    with pytest.raises(ValueError):
        ProductAdapter.from_rabbitmq_message(invalid_message)


def test_from_rabbitmq_message_invalid_element_data():
    """Test handling of invalid element data in RabbitMQ message."""
    # Given
    message_with_invalid_element = {
        "productId": "P12345",
        "productName": "Test Product",
        "productElements": [
            {
                "Lenght": "invalid",  # Should be integer
                "Procuct Element": "Test Element",
                "Type": "Hardware",
                "GG Startup": 3,
                "RU": "RU1",
                "RU Qty": 10,
                "RU Unit of measure": "Days",
                "Q.ty min": 1,
                "Q.ty MAX": 100,
                "%Sconto MAX": "invalid",  # Should be numeric
                "Status": "Active"
            }
        ]
    }

    # When/Then
    with pytest.raises(ValueError):
        ProductAdapter.from_rabbitmq_message(message_with_invalid_element)