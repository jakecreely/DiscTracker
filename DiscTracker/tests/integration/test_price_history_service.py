from datetime import date
from django.db import DatabaseError
from unittest.mock import patch

import pytest
from items.services.price_history_service import PriceHistoryService
from items.models.db_models import Item, PriceHistory


@pytest.fixture
def price_history_service():
    return PriceHistoryService()


@pytest.fixture
def existing_item():
    return Item.objects.create(
        cex_id="5060020626449",
        title="Halloween (18) 1978",
        sell_price=8.0,
        exchange_price=5.0,
        cash_price=3.0,
        last_checked=date(2025, 1, 1),
    )


@pytest.mark.django_db
def test_create_price_history_entry_success(price_history_service, existing_item):
    price_entry = price_history_service.create_price_history_entry(existing_item)

    assert price_entry.item == existing_item
    assert price_entry.sell_price == existing_item.sell_price
    assert price_entry.exchange_price == existing_item.exchange_price
    assert price_entry.cash_price == existing_item.cash_price


@pytest.mark.django_db
def test_create_price_history_entry_falsey_input(price_history_service):
    price_entry = price_history_service.create_price_history_entry(None)

    assert price_entry is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
def test_create_price_history_entry_invalid_item(price_history_service):
    invalid_object = {"one": 1, "two": 2}

    price_entry = price_history_service.create_price_history_entry(invalid_object)

    assert price_entry is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
@patch("items.models.db_models.PriceHistory.objects.create")
def test_create_price_history_entry_database_error(
    mock_create, price_history_service, existing_item
):
    mock_create.side_effect = DatabaseError

    price_entry = price_history_service.create_price_history_entry(existing_item)

    price_entry is None


@pytest.mark.django_db
@patch("items.models.db_models.PriceHistory.objects.create")
def test_create_price_history_entry_unexpected_error(
    mock_create, price_history_service, existing_item
):
    mock_create.side_effect = Exception

    price_entry = price_history_service.create_price_history_entry(existing_item)

    assert price_entry is None


@pytest.mark.django_db
def test_create_price_history_if_price_changed_no_latest_history(
    price_history_service, existing_item
):
    PriceHistory.objects.filter(item=existing_item).delete()

    price_history_entry = price_history_service.create_price_history_if_price_changed(
        existing_item
    )

    assert price_history_entry is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
def test_create_price_history_if_price_changed_price_changed(
    price_history_service, existing_item
):
    PriceHistory.objects.create(
        item=existing_item,
        sell_price=7.0,
        exchange_price=4.0,
        cash_price=2.0,
        date_checked=date(2024, 1, 1),
    )

    price_history_entry = price_history_service.create_price_history_if_price_changed(
        existing_item
    )

    assert price_history_entry is not None
    assert price_history_entry.sell_price == 8.0
    assert price_history_entry.exchange_price == 5.0
    assert price_history_entry.cash_price == 3.0
    assert PriceHistory.objects.count() == 2


@pytest.mark.django_db
def test_create_price_history_if_price_changed_price_not_changed(
    price_history_service, existing_item
):
    PriceHistory.objects.create(
        item=existing_item,
        sell_price=8.0,
        exchange_price=5.0,
        cash_price=3.0,
        date_checked=date(2024, 1, 1),
    )

    price_history_entry = price_history_service.create_price_history_if_price_changed(
        existing_item
    )

    assert price_history_entry is None
    assert PriceHistory.objects.count() == 1


@pytest.mark.django_db
def test_has_price_changed_true(price_history_service, existing_item):
    assert price_history_service.has_price_changed(existing_item, 9.0, 5.0, 3.0) is True
    assert price_history_service.has_price_changed(existing_item, 8.0, 6.0, 3.0) is True
    assert price_history_service.has_price_changed(existing_item, 8.0, 5.0, 4.0) is True


@pytest.mark.django_db
def test_has_price_changed_false(price_history_service, existing_item):
    assert (
        price_history_service.has_price_changed(existing_item, 8.0, 5.0, 3.0) is False
    )
