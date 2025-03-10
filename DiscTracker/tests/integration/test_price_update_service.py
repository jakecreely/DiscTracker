import pytest
import requests
from datetime import date
from unittest.mock import patch
from items.services.price_update_service import PriceUpdateService
from items.services.item_service import ItemService
from items.services.user_item_service import UserItemService
from items.services.price_history_service import PriceHistoryService
from items.services.cex_service import CexService
from items.validators.item_validator import ItemDataValidator
from items.models.pydantic_models import ItemData
from items.models.db_models import Item


@pytest.fixture
def existing_item():
    return Item.objects.create(
        cex_id="123456",
        title="Valid Item",
        sell_price=20.0,
        exchange_price=15.0,
        cash_price=10.0,
        last_checked=date(2024, 12, 31),
    )


@pytest.fixture
def price_update_service():
    validator = ItemDataValidator()
    user_item_service = UserItemService()
    price_history_service = PriceHistoryService()

    item_service = ItemService(
        validator=validator,
        user_item_service=user_item_service,
        price_history_service=price_history_service,
    )

    cex_service = CexService()

    return PriceUpdateService(
        item_service=item_service,
        api_service=cex_service,
        price_history_service=price_history_service,
    )


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_single_item(
    mock_fetch_item, price_update_service, existing_item
):
    mock_fetch_item.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=15.0,
        exchange_price=3.0,
        cash_price=8.0,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == 15.0
    assert updated_item.exchange_price == 3.0
    assert updated_item.cash_price == 8.0

    # DB Check
    updated_item.refresh_from_db()
    updated_item.sell_price == 15.0
    updated_item.exchange_price == 3.0
    updated_item.cash_price == 8.0


@pytest.mark.skip(reason="Test not implemented")
def test_check_price_updates_multiple_items(self):
    self.assertIsNotNone(None)


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_no_price_change(
    mock_fetch, price_update_service, existing_item
):
    current_sell_price = existing_item.sell_price
    current_exchange_price = existing_item.exchange_price
    current_cash_price = existing_item.cash_price

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=current_sell_price,
        exchange_price=current_exchange_price,
        cash_price=current_cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 0

    # Check DB
    existing_item.refresh_from_db()
    assert existing_item.sell_price == current_sell_price
    assert existing_item.exchange_price == current_exchange_price
    assert existing_item.cash_price == current_cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_cash_price_decreases(
    mock_fetch, price_update_service, existing_item
):
    decreased_cash_price = max(existing_item.cash_price - 1, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=existing_item.sell_price,
        exchange_price=existing_item.exchange_price,
        cash_price=decreased_cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == existing_item.sell_price
    assert updated_item.exchange_price == existing_item.exchange_price
    assert updated_item.cash_price == decreased_cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == existing_item.sell_price
    assert updated_item.exchange_price == existing_item.exchange_price
    assert updated_item.cash_price == decreased_cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_sell_price_increases(
    mock_fetch, price_update_service, existing_item
):
    increased_sell_price = max(existing_item.sell_price + 10.5, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=increased_sell_price,
        exchange_price=existing_item.exchange_price,
        cash_price=existing_item.cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == increased_sell_price
    assert updated_item.exchange_price == existing_item.exchange_price
    assert updated_item.cash_price == existing_item.cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == increased_sell_price
    assert updated_item.exchange_price == existing_item.exchange_price
    assert updated_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_sell_price_decreases(
    mock_fetch, price_update_service, existing_item
):
    decreased_sell_price = max(existing_item.sell_price - 1, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=decreased_sell_price,
        exchange_price=existing_item.exchange_price,
        cash_price=existing_item.cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == decreased_sell_price
    assert updated_item.exchange_price == existing_item.exchange_price
    assert updated_item.cash_price == existing_item.cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == decreased_sell_price
    assert updated_item.exchange_price == existing_item.exchange_price
    assert updated_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_exchange_price_increases(
    mock_fetch, price_update_service, existing_item
):
    increased_exchange_price = max(existing_item.exchange_price + 10.5, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=existing_item.sell_price,
        exchange_price=increased_exchange_price,
        cash_price=existing_item.cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == existing_item.sell_price
    assert updated_item.exchange_price == increased_exchange_price
    assert updated_item.cash_price == existing_item.cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == existing_item.sell_price
    assert updated_item.exchange_price == increased_exchange_price
    assert updated_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_exchange_price_decreases(
    mock_fetch, price_update_service, existing_item
):
    decreased_exchange_price = max(existing_item.exchange_price - 1, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=existing_item.sell_price,
        exchange_price=decreased_exchange_price,
        cash_price=existing_item.cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == existing_item.sell_price
    assert updated_item.exchange_price == decreased_exchange_price
    assert updated_item.cash_price == existing_item.cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == existing_item.sell_price
    assert updated_item.exchange_price == decreased_exchange_price
    assert updated_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_all_prices_increase(
    mock_fetch, price_update_service, existing_item
):
    increased_sell_price = max(existing_item.sell_price + 1, 0)
    increased_exchange_price = max(existing_item.exchange_price + 2, 0)
    increased_cash_price = max(existing_item.cash_price + 3, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=increased_sell_price,
        exchange_price=increased_exchange_price,
        cash_price=increased_cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == increased_sell_price
    assert updated_item.exchange_price == increased_exchange_price
    assert updated_item.cash_price == increased_cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == increased_sell_price
    assert updated_item.exchange_price == increased_exchange_price
    assert updated_item.cash_price == increased_cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_all_prices_decrease(
    mock_fetch, price_update_service, existing_item
):
    decreased_sell_price = max(existing_item.sell_price - 1, 0)
    decreased_exchange_price = max(existing_item.exchange_price - 2, 0)
    decreased_cash_price = max(existing_item.cash_price - 3, 0)

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=decreased_sell_price,
        exchange_price=decreased_exchange_price,
        cash_price=decreased_cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 1

    updated_item = updated_items[0]

    # Check Response
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == existing_item.title
    assert updated_item.sell_price == decreased_sell_price
    assert updated_item.exchange_price == decreased_exchange_price
    assert updated_item.cash_price == decreased_cash_price

    # DB Check
    updated_item.refresh_from_db()
    assert updated_item.sell_price == decreased_sell_price
    assert updated_item.exchange_price == decreased_exchange_price
    assert updated_item.cash_price == decreased_cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_all_prices_negative(
    mock_fetch, price_update_service, existing_item
):
    negative_sell_price = -1.0
    negative_exchange_price = -1.0
    negative_cash_price = -1.0

    mock_fetch.return_value = ItemData(
        cex_id=existing_item.cex_id,
        title=existing_item.title,
        sell_price=negative_sell_price,
        exchange_price=negative_exchange_price,
        cash_price=negative_cash_price,
    )

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 0

    # DB Check
    existing_item.refresh_from_db()
    assert existing_item.cex_id == existing_item.cex_id
    assert existing_item.title == existing_item.title
    assert existing_item.sell_price != negative_sell_price
    assert existing_item.exchange_price != negative_exchange_price
    assert existing_item.cash_price != negative_cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_no_items_to_check(mock_fetch, price_update_service):
    Item.objects.all().delete()

    updated_items = price_update_service.check_price_updates()

    assert len(updated_items) == 0

    mock_fetch.assert_not_called()


# @pytest.mark.django_db
# @patch("items.services.cex_service.CexService.fetch_item")
# def test_check_price_updates_incorrect_format(mock_fetch, price_update_service, existing_item):
#     increased_exchange_price = existing_item.exchange_price + 10
#     increased_cash_price = existing_item.cash_price + 10

#     mock_fetch.return_value = ItemData(
#         cex_id=existing_item.cex_id,
#         # Missing - "title": existing_item.title,
#         # Missing - "sell_price": existing_item.sell_price,
#         exchange_price=increased_exchange_price,
#         cash_price=increased_cash_price,
#     )

#     updated_items = price_update_service.check_price_updates()

#     # Invalid Items are skipped
#     assert len(updated_items) == 0

#     existing_item.refresh_from_db()
#     assert existing_item.cex_id == existing_item.cex_id
#     assert existing_item.title == existing_item.title
#     assert existing_item.exchange_price != increased_exchange_price
#     assert existing_item.cash_price != increased_cash_price


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_http_error(mock_fetch_item, price_update_service):
    mock_fetch_item.side_effect = requests.exceptions.HTTPError

    updated_items = price_update_service.check_price_updates()

    assert updated_items == []


@pytest.mark.django_db
@patch("items.services.item_service.ItemService.get_all_items")
def test_check_price_updates_json_error(mock_get_all_items, price_update_service):
    mock_get_all_items.side_effect = requests.exceptions.JSONDecodeError(
        "Expecting value", "", 0
    )

    updated_items = price_update_service.check_price_updates()

    assert updated_items is None


@pytest.mark.django_db
@patch("items.services.cex_service.CexService.fetch_item")
def test_check_price_updates_unexpected_error_inner(
    mock_fetch_item, price_update_service
):
    mock_fetch_item.side_effect = Exception

    updated_items = price_update_service.check_price_updates()

    assert updated_items == []


@pytest.mark.django_db
@patch("items.services.item_service.ItemService.get_all_items")
def test_check_price_updates_unexpected_error_outer(
    mock_get_all_items, price_update_service
):
    mock_get_all_items.side_effect = Exception

    updated_items = price_update_service.check_price_updates()

    assert updated_items is None
