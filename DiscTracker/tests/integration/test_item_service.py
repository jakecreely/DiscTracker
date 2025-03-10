from datetime import date
from django.db import DatabaseError
from unittest.mock import patch
from django.contrib.auth import get_user_model

import pytest
from items.services.item_service import ItemService
from items.services.user_item_service import UserItemService
from items.services.price_history_service import PriceHistoryService
from items.validators.item_validator import ItemDataValidator
from items.models.db_models import Item, UserItem, PriceHistory


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        username="testuser", password="testpass"
    )


@pytest.fixture
def item_service():
    validator = ItemDataValidator()
    user_item_service = UserItemService()
    price_history_service = PriceHistoryService()

    return ItemService(
        validator=validator,
        user_item_service=user_item_service,
        price_history_service=price_history_service,
    )


@pytest.fixture
def existing_item_fetched_data():
    return {
        "cex_id": "5060020626449",
        "title": "Halloween (18) 1978",
        "sell_price": 8.0,
        "exchange_price": 5.0,
        "cash_price": 3.0,
    }


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


@pytest.fixture
def valid_fetched_item_data():
    return {
        "cex_id": "5050582577013",
        "title": "Thing, The (18) 1982",
        "sell_price": 6.0,
        "exchange_price": 2.0,
        "cash_price": 1.5,
    }


def test_get_item_by_cex_id_success(item_service, existing_item):
    item = item_service.get_item_by_cex_id(existing_item.cex_id)

    assert item is not None
    assert item.cex_id == existing_item.cex_id
    assert item.title == existing_item.title
    assert item.sell_price == existing_item.sell_price
    assert item.exchange_price == existing_item.exchange_price
    assert item.cash_price == existing_item.cash_price


@pytest.mark.django_db
def test_get_item_by_cex_id_not_found(item_service):
    item = item_service.get_item_by_cex_id("nonexistent_cex_id")

    assert item is None


@pytest.mark.django_db
def test_get_all_items(item_service, existing_item):
    items = item_service.get_all_items()

    assert items.count() == 1
    assert items[0].cex_id == existing_item.cex_id
    assert items[0].title == existing_item.title
    assert items[0].sell_price == existing_item.sell_price
    assert items[0].exchange_price == existing_item.exchange_price
    assert items[0].cash_price == existing_item.cash_price


@pytest.mark.django_db
def test_get_user_items(item_service, user, existing_item):
    UserItem.objects.create(user=user, item=existing_item)

    user_items = item_service.get_user_items(user)

    assert user_items.count() == 1
    assert user_items[0].cex_id == existing_item.cex_id
    assert user_items[0].title == existing_item.title
    assert user_items[0].sell_price == existing_item.sell_price
    assert user_items[0].exchange_price == existing_item.exchange_price
    assert user_items[0].cash_price == existing_item.cash_price


@pytest.mark.django_db
def test_get_user_items_invalid_user(item_service):
    invalid_user = "invalid_user"

    with pytest.raises(ValueError):
        item_service.get_user_items(invalid_user)


@pytest.mark.django_db
def test_create_item_success(item_service, valid_fetched_item_data):
    item, item_created = item_service.create_item(valid_fetched_item_data)

    assert item is not None
    assert item_created is True
    assert item.cex_id == valid_fetched_item_data["cex_id"]
    assert item.title == valid_fetched_item_data["title"]
    assert item.sell_price == valid_fetched_item_data["sell_price"]
    assert item.exchange_price == valid_fetched_item_data["exchange_price"]
    assert item.cash_price == valid_fetched_item_data["cash_price"]

    # Check DB has created item correctly
    db_item = Item.objects.get(cex_id=item.cex_id)
    assert db_item.title == valid_fetched_item_data["title"]
    assert db_item.sell_price == valid_fetched_item_data["sell_price"]
    assert db_item.exchange_price == valid_fetched_item_data["exchange_price"]
    assert db_item.cash_price == valid_fetched_item_data["cash_price"]


# @pytest.mark.django_db
# def test_create_item_invalid_id(item_service):
#     invalid_fetched_item_data = {
#         "cex_id": "-1",  # Invalid ID
#         "title": "Thing, The (18) 1982",
#         "sell_price": 6.0,
#         "exchange_price": 2.0,
#         "cash_price": 1.5,
#     }

#     item, item_created = item_service.create_item(
#         invalid_fetched_item_data
#     )

#     assert item is None
#     assert item_created is False


@pytest.mark.django_db
def test_create_item_missing_attributes(item_service):
    fetched_item_data = {
        "cex_id": "5050582577013",
        "exchange_price": 2.0,
        "cash_price": 1.5,
    }

    item, item_created = item_service.create_item(fetched_item_data)

    assert item is None
    assert item_created is False


@pytest.mark.django_db
def test_update_item_success(item_service, existing_item):
    update_item_data = {
        "cex_id": existing_item.cex_id,
        "title": "Updated Title",
        "sell_price": 20.0,
        "exchange_price": 12.50,
        "cash_price": 10.0,
    }

    updated_item = item_service.update_item(update_item_data)

    assert updated_item is not None
    assert updated_item.cex_id == existing_item.cex_id
    assert updated_item.title == update_item_data["title"]
    assert updated_item.sell_price == update_item_data["sell_price"]
    assert updated_item.exchange_price == update_item_data["exchange_price"]
    assert updated_item.cash_price == update_item_data["cash_price"]

    # Check DB has updated correctly
    db_item = Item.objects.get(cex_id=existing_item.cex_id)
    assert db_item.title == update_item_data["title"]
    assert db_item.sell_price == update_item_data["sell_price"]
    assert db_item.exchange_price == update_item_data["exchange_price"]
    assert db_item.cash_price == update_item_data["cash_price"]


@pytest.mark.django_db
def test_update_item_invalid_id(item_service, existing_item):
    update_item_data = {
        "cex_id": "-1",  # Invalid ID
        "title": "Updated Title",
        "sell_price": 20.0,
        "exchange_price": 12.50,
        "cash_price": 10.0,
    }

    updated_item = item_service.update_item(update_item_data)

    assert updated_item is None

    # Verify existing item remains unchanged
    db_item = Item.objects.get(cex_id=existing_item.cex_id)
    assert db_item.title == existing_item.title
    assert db_item.sell_price == existing_item.sell_price
    assert db_item.exchange_price == existing_item.exchange_price
    assert db_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
def test_update_item_missing_attributes(item_service, existing_item):
    update_item_data = {
        "cex_id": existing_item.cex_id,
        "title": "Updated Title",
        "sell_price": 20.0,
        # Missing - "exchange_price": 12.50,
        # Missing - "cash_price": 10.0
    }

    updated_item = item_service.update_item(update_item_data)

    assert updated_item is None

    # Check DB has remains unchanged
    db_item = Item.objects.get(cex_id=existing_item.cex_id)
    assert db_item.title == existing_item.title
    assert db_item.sell_price == existing_item.sell_price
    assert db_item.exchange_price == existing_item.exchange_price
    assert db_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
def test_update_item_none_input(item_service):
    item = item_service.update_item(None)

    assert item is None


@pytest.mark.django_db
@patch("items.models.db_models.Item.save")
def test_update_item_database_error(mock_save, item_service, existing_item):
    update_item_data = {
        "cex_id": existing_item.cex_id,
        "title": "Updated Title",
        "sell_price": 20.0,
        "exchange_price": 12.50,
        "cash_price": 10.0,
    }

    mock_save.side_effect = DatabaseError
    item = item_service.update_item(update_item_data)

    assert item is None

    db_item = Item.objects.get(cex_id=existing_item.cex_id)
    assert db_item.title == existing_item.title
    assert db_item.sell_price == existing_item.sell_price
    assert db_item.exchange_price == existing_item.exchange_price
    assert db_item.cash_price == existing_item.cash_price


@pytest.mark.django_db
@patch("items.models.db_models.Item.save")
def test_update_item_unexpected_error(mock_save, item_service, existing_item):
    update_item_data = {
        "cex_id": existing_item.cex_id,
        "title": "Updated Title",
        "sell_price": 20.0,
        "exchange_price": 12.50,
        "cash_price": 10.0,
    }

    mock_save.side_effect = Exception
    item = item_service.update_item(update_item_data)

    assert item is None

    db_item = Item.objects.get(cex_id=existing_item.cex_id)
    assert db_item.title == existing_item.title
    assert db_item.sell_price == existing_item.sell_price
    assert db_item.exchange_price == existing_item.exchange_price
    assert db_item.cash_price == existing_item.cash_price


# def test_create_or_update_item_one_item_multiple_users(self):
#     user_two = get_user_model().objects.create_user(
#         username="user2", password="testpass2"
#     )

#     same_as_existing_item = {
#         "boxId": self.existing_item.cex_id,
#         "boxName": self.existing_item.title,
#         "sellPrice": self.existing_item.sell_price,
#         "exchangePrice": self.existing_item.exchange_price,
#         "cashPrice": self.existing_item.cash_price,
#     }

#     # self.user already has self.existing_item
#     item = cex.create_or_update_item(same_as_existing_item, user_two)

#     self.assertIsNotNone(item)
#     self.assertEqual(item.cex_id, self.existing_item.cex_id)
#     self.assertEqual(item.title, self.existing_item.title)
#     self.assertEqual(item.sell_price, self.existing_item.sell_price)
#     self.assertEqual(item.exchange_price, self.existing_item.exchange_price)
#     self.assertEqual(item.cash_price, self.existing_item.cash_price)

#     user_one_item_exists = UserItem.objects.filter(
#         user=self.user, item=self.existing_item
#     ).exists()
#     self.assertTrue(user_one_item_exists)

#     user_two_item_exists = UserItem.objects.filter(
#         user=user_two, item=self.existing_item
#     ).exists()
#     self.assertTrue(user_two_item_exists)


@pytest.mark.django_db
def test_delete_item_success(item_service, existing_item):
    item_deleted = item_service.delete_item(existing_item.cex_id)

    assert item_deleted is True

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is None


@pytest.mark.django_db
def test_delete_item_id_is_none(item_service, existing_item):
    item_deleted = item_service.delete_item(None)

    assert item_deleted is False

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is not None


@pytest.mark.django_db
def test_delete_item_invalid_id(item_service, existing_item):
    item_deleted = item_service.delete_item("-1")

    assert item_deleted is False

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is not None


@pytest.mark.django_db
@patch("items.models.db_models.Item.delete")
def test_delete_item_item_is_none(mock_delete, item_service, existing_item):
    mock_delete.side_effect = None

    item_deleted = item_service.delete_item(existing_item.cex_id)

    assert item_deleted is False


@pytest.mark.django_db
@patch("items.models.db_models.Item.delete")
def test_delete_item_deleted_count_eq_0(mock_delete, item_service, existing_item):
    mock_delete.return_value = (0, None)

    item_deleted = item_service.delete_item(existing_item.cex_id)

    assert item_deleted is False

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is not None


@pytest.mark.django_db
@patch("items.models.db_models.Item.delete")
def test_delete_item_deleted_count_gt_1(mock_delete, item_service, existing_item):
    mock_delete.return_value = (3, None)

    item_deleted = item_service.delete_item(existing_item.cex_id)

    assert item_deleted is False

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is not None


# def test_delete_item_multiple_users(self):
#     user_1 = get_user_model().objects.create(username="user1", password="pass1")
#     user_2 = get_user_model().objects.create(username="user2", password="pass2")

#     UserItem.objects.create(user=user_1, item=self.existing_item)
#     UserItem.objects.create(user=user_2, item=self.existing_item)

#     item_deleted = cex.delete_item(self.existing_item.cex_id, user_1)

#     self.assertTrue(item_deleted)

#     user_item_1_exists = UserItem.objects.filter(
#         user=user_1, item=self.existing_item
#     ).exists()
#     user_item_2_exists = UserItem.objects.filter(
#         user=user_2, item=self.existing_item
#     ).exists()

#     # User 1 doesn't have item but User 2 still does
#     self.assertFalse(user_item_1_exists)
#     self.assertTrue(user_item_2_exists)


@pytest.mark.django_db
@patch("items.models.db_models.Item.delete")
def test_delete_item_database_error(mock_delete, item_service, existing_item):
    mock_delete.side_effect = DatabaseError

    item_deleted = item_service.delete_item(existing_item.cex_id)

    assert item_deleted is False

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is not None


@pytest.mark.django_db
@patch("items.models.db_models.Item.delete")
def test_delete_item_unknown_exception(mock_delete, item_service, existing_item):
    mock_delete.side_effect = Exception

    item_deleted = item_service.delete_item(existing_item.cex_id)

    assert item_deleted is False

    assert item_service.get_item_by_cex_id(existing_item.cex_id) is not None


@pytest.mark.django_db
def test_create_item_and_price_history_invalid_item_data(item_service, user):
    invalid_item_data = {"invalid": "data"}

    item, price_history_entry = item_service.create_item_and_price_history(
        invalid_item_data, user
    )

    assert item is None
    assert price_history_entry is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
def test_create_item_and_price_history_item_is_none(item_service, user):
    item, price_history_entry = item_service.create_item_and_price_history(None, user)

    assert item is None
    assert price_history_entry is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
def test_create_item_and_price_history_invalid_user(
    item_service, valid_fetched_item_data
):
    invalid_user = "invalid_user"

    item, price_history_entry = item_service.create_item_and_price_history(
        valid_fetched_item_data, invalid_user
    )

    assert item is None
    assert price_history_entry is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
def test_create_item_and_price_history_no_price_history(
    item_service, valid_fetched_item_data, user
):
    item, price_history_entry = item_service.create_item_and_price_history(
        valid_fetched_item_data, user
    )

    assert item is not None
    assert item.cex_id == valid_fetched_item_data["cex_id"]
    assert item.title == valid_fetched_item_data["title"]
    assert item.sell_price == valid_fetched_item_data["sell_price"]
    assert item.exchange_price == valid_fetched_item_data["exchange_price"]
    assert item.cash_price == valid_fetched_item_data["cash_price"]

    assert price_history_entry is not None
    assert price_history_entry.item == item
    assert price_history_entry.sell_price == valid_fetched_item_data["sell_price"]
    assert (
        price_history_entry.exchange_price == valid_fetched_item_data["exchange_price"]
    )
    assert price_history_entry.cash_price == valid_fetched_item_data["cash_price"]

    assert PriceHistory.objects.count() == 1


@pytest.mark.django_db
def test_create_item_and_price_history_existing_price_history_change(
    item_service, user, existing_item_fetched_data, existing_item
):
    PriceHistory.objects.create(
        item=existing_item,
        sell_price=1.0,
        exchange_price=1.0,
        cash_price=1.0,
        date_checked=date(2025, 1, 1),
    )

    item, price_history_entry = item_service.create_item_and_price_history(
        existing_item_fetched_data, user
    )

    assert item is not None
    assert item.cex_id == existing_item.cex_id
    assert item.title == existing_item.title
    assert item.sell_price == existing_item.sell_price
    assert item.exchange_price == existing_item.exchange_price
    assert item.cash_price == existing_item.cash_price

    assert price_history_entry is not None
    assert price_history_entry.item == item
    assert price_history_entry.sell_price == existing_item.sell_price
    assert price_history_entry.exchange_price == existing_item.exchange_price
    assert price_history_entry.cash_price == existing_item.cash_price

    assert PriceHistory.objects.count() == 2


@pytest.mark.django_db
def test_create_item_and_price_history_existing_price_history_no_change(
    item_service, existing_item_fetched_data, user, existing_item
):
    PriceHistory.objects.create(
        item=existing_item,
        sell_price=existing_item.sell_price,
        exchange_price=existing_item.exchange_price,
        cash_price=existing_item.cash_price,
        date_checked=date(2025, 1, 1),
    )

    item, price_history_entry = item_service.create_item_and_price_history(
        existing_item_fetched_data, user
    )

    assert item is not None
    assert item.cex_id == existing_item.cex_id
    assert item.title == existing_item.title
    assert item.sell_price == existing_item.sell_price
    assert item.exchange_price == existing_item.exchange_price
    assert item.cash_price == existing_item.cash_price

    assert price_history_entry is None

    assert PriceHistory.objects.count() == 1


@pytest.mark.django_db
@patch("items.models.db_models.Item.objects.get_or_create")
def test_create_item_and_price_history_failed_to_create_item(
    mock_get_or_create, item_service, valid_fetched_item_data, user
):
    mock_get_or_create.return_value = None

    item, price_history_entry = item_service.create_item_and_price_history(
        valid_fetched_item_data, user
    )

    assert item is None
    assert price_history_entry is None

    assert item_service.get_item_by_cex_id(valid_fetched_item_data["cex_id"]) is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
@patch("items.models.db_models.PriceHistory.objects.create")
def test_create_item_and_price_history_failed_to_create_price_history(
    mock_create, item_service, valid_fetched_item_data, user
):
    mock_create.return_value = None

    item, price_history_entry = item_service.create_item_and_price_history(
        valid_fetched_item_data, user
    )

    assert item is None
    assert price_history_entry is None

    assert item_service.get_item_by_cex_id(valid_fetched_item_data["cex_id"]) is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
@patch("items.services.item_service.ItemService.create_item")
def test_create_item_and_price_history_database_error(
    mock_call, item_service, valid_fetched_item_data, user
):
    mock_call.side_effect = DatabaseError

    item, price_history_entry = item_service.create_item_and_price_history(
        valid_fetched_item_data, user
    )

    assert item is None
    assert price_history_entry is None

    assert item_service.get_item_by_cex_id(valid_fetched_item_data["cex_id"]) is None
    assert PriceHistory.objects.count() == 0


@pytest.mark.django_db
@patch("items.services.item_service.ItemService.create_item")
def test_create_or_update_item_and_price_history_unknown_exception(
    mock_call, item_service, valid_fetched_item_data, user
):
    mock_call.side_effect = Exception

    item, price_history_entry = item_service.create_item_and_price_history(
        valid_fetched_item_data, user
    )

    assert item is None
    assert price_history_entry is None

    assert item_service.get_item_by_cex_id(valid_fetched_item_data["cex_id"]) is None
    assert PriceHistory.objects.count() == 0
