from datetime import date
from django.db import DatabaseError
from unittest.mock import patch
import pytest
from items.services.user_item_service import UserItemService
from items.models.db_models import Item, UserItem
from django.contrib.auth import get_user_model


@pytest.fixture
@pytest.mark.django_db
def user_item_service():
    return UserItemService()


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        username="testuser", password="testpass"
    )


@pytest.fixture
def item():
    return Item.objects.create(
        cex_id="5060020626449",
        title="Halloween (18) 1978",
        sell_price=8.0,
        exchange_price=5.0,
        cash_price=3.0,
        last_checked=date(2025, 1, 1),
    )


@pytest.mark.django_db
def test_user_owns_item(user_item_service, user, item):
    UserItem.objects.create(user=user, item=item)
    assert user_item_service.user_owns_item(user, item) is True


@pytest.mark.django_db
def test_user_does_not_own_item(user_item_service, user, item):
    assert user_item_service.user_owns_item(user, item) is False


@pytest.mark.django_db
def test_add_user_item_success(user_item_service, user, item):
    user_item = user_item_service.add_user_item(user, item)
    assert user_item is not None
    assert user_item_service.user_owns_item(user, item) is True


@pytest.mark.django_db
def test_add_user_item_already_exists(user_item_service, user, item):
    UserItem.objects.create(user=user, item=item)
    user_item = user_item_service.add_user_item(user, item)
    assert user_item is None


# @pytest.mark.django_db
# @patch("items.models.db_models.UserItem.objects.create")
# def test_add_user_item_database_error(mock_create, user_item_service, user, item):
#     mock_create.side_effect = Exception
#     user_item = user_item_service.add_user_item(user, item)
#     assert user_item is None


@pytest.mark.django_db
def test_delete_user_item_success(user_item_service, user, item):
    UserItem.objects.create(user=user, item=item)
    assert user_item_service.delete_user_item(user, item) is True
    assert user_item_service.user_owns_item(user, item) is False


@pytest.mark.django_db
def test_delete_user_item_not_owned(user_item_service, user, item):
    assert user_item_service.delete_user_item(user, item) is False


@pytest.mark.django_db
@patch("items.models.db_models.UserItem.objects.filter")
def test_delete_user_item_database_error(mock_filter, user_item_service, user, item):
    mock_filter.side_effect = DatabaseError
    assert user_item_service.delete_user_item(user, item) is False
