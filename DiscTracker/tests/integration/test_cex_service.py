import pytest
import requests
from datetime import date
from django.test import TestCase
from django.db import DatabaseError
from django.contrib.auth import get_user_model
from unittest.mock import patch
from items.services import cex
from items.models.db_models import Item, UserItem, PriceHistory


class TestCexServiceFetchItem(TestCase):
    @patch("items.services.cex.requests.get")
    def test_fetch_item_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": "711719417576",
                            "boxName": "Spider-Man (2018) No DLC",
                            "sellPrice": 15.0,
                            "exchangePrice": 10.0,
                            "cashPrice": 7.0,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        result = cex.fetch_item("711719417576")

        self.assertIsNotNone(result)
        self.assertEqual(result.boxId, "711719417576")
        self.assertEqual(result.boxName, "Spider-Man (2018) No DLC")
        self.assertEqual(result.sellPrice, 15.0)
        self.assertEqual(result.exchangePrice, 10.0)
        self.assertEqual(result.cashPrice, 7.0)

    @patch("items.services.cex.requests.get")
    def test_fetch_item_invalid_cex_id(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.json.return_value = {
            "response": {
                "data": "",
                "error": {
                    "code": 12,
                    "internal_message": "Service not found",
                    "moreInfo": [],
                },
            }
        }

        invalid_cex_id = "-1"
        result = cex.fetch_item(invalid_cex_id)

        self.assertIsNone(result)

    @patch("items.services.cex.requests.get")
    def test_fetch_item_invalid_response_schema(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                # Missing - "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": "711719417576",
                            "boxName": "Spider-Man (2018) No DLC",
                            "sellPrice": 15.0,
                            "exchangePrice": 10.0,
                            "cashPrice": 7.0,
                        }
                    ]
                },
                # Missing - "error": {
                #     "code": "",
                #     "internal_message": "",
                #     "moreInfo": []
                # }
            }
        }

        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)

    @patch("items.services.cex.requests.get")
    def test_fetch_item_additional_attributes(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": "711719417576",
                            "boxName": "Spider-Man (2018) No DLC",
                            "sellPrice": 15.0,
                            "exchangePrice": 10.0,
                            "cashPrice": 7.0,
                            "extraField": "extraInfo",
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        result = cex.fetch_item("711719417576")

        self.assertIsNotNone(result)
        self.assertEqual(result.boxId, "711719417576")
        self.assertEqual(result.boxName, "Spider-Man (2018) No DLC")
        self.assertEqual(result.sellPrice, 15.0)
        self.assertEqual(result.exchangePrice, 10.0)
        self.assertEqual(result.cashPrice, 7.0)
        self.assertNotIn("extraField", result)

    @patch("items.services.cex.requests.get")
    def test_fetch_item_http_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError
        )

        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)

    @patch("items.services.cex.requests.get")
    def test_fetch_item_json_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = (
            requests.exceptions.JSONDecodeError("", "", 0)
        )

        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)

    @patch("items.services.cex.requests.get")
    def test_fetch_item_unexpected_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = Exception

        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)


class TestCexServiceCreateOrUpdateItem(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )

        self.existing_item = Item.objects.create(
            cex_id="5060020626449",
            title="Halloween (18) 1978",
            sell_price=8.0,
            exchange_price=5.0,
            cash_price=3.0,
            last_checked=date(2025, 1, 1),
        )

        self.user_existing_item = UserItem.objects.get_or_create(
            user=self.user,
            item=self.existing_item,
        )

        self.valid_fetched_item_data = {
            "boxId": "5050582577013",
            "boxName": "Thing, The (18) 1982",
            "sellPrice": 6.0,
            "exchangePrice": 2.0,
            "cashPrice": 1.5,
        }

    def test_create_item_success(self):
        created_item = cex.create_or_update_item(
            self.valid_fetched_item_data, self.user
        )

        self.assertIsNotNone(created_item)
        self.assertEqual(created_item.cex_id, self.valid_fetched_item_data["boxId"])
        self.assertEqual(created_item.title, self.valid_fetched_item_data["boxName"])
        self.assertEqual(
            created_item.sell_price, self.valid_fetched_item_data["sellPrice"]
        )
        self.assertEqual(
            created_item.exchange_price, self.valid_fetched_item_data["exchangePrice"]
        )
        self.assertEqual(
            created_item.cash_price, self.valid_fetched_item_data["cashPrice"]
        )

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=created_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_create_item_invalid_id(self):
        invalid_fetched_item_data = {
            "boxId": "-1",  # Invalid ID
            "boxName": "Thing, The (18) 1982",
            "sellPrice": 6.0,
            "exchangePrice": 2.0,
            "cashPrice": 1.5,
        }

        created_item = cex.create_or_update_item(
            invalid_fetched_item_data, user=self.user
        )

        self.assertIsNone(created_item)

    def test_create_item_missing_attributes(self):
        fetched_item_data = {
            "boxId": "5050582577013",
            "exchangePrice": 2.0,
            "cashPrice": 1.5,
        }

        created_item = cex.create_or_update_item(fetched_item_data, user=self.user)

        self.assertIsNone(created_item)

    def test_update_item_success(self):
        update_item_data = {
            "boxId": self.existing_item.cex_id,
            "boxName": "Updated Title",
            "sellPrice": 20.0,
            "exchangePrice": 12.50,
            "cashPrice": 10.0,
        }

        updated_item = cex.create_or_update_item(update_item_data, user=self.user)

        self.assertIsNotNone(updated_item)
        self.assertEqual(
            updated_item.cex_id, self.existing_item.cex_id
        )  # ID remains the same
        self.assertEqual(updated_item.title, update_item_data["boxName"])
        self.assertEqual(updated_item.sell_price, update_item_data["sellPrice"])
        self.assertEqual(updated_item.exchange_price, update_item_data["exchangePrice"])
        self.assertEqual(updated_item.cash_price, update_item_data["cashPrice"])

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=updated_item
        ).exists()
        self.assertTrue(user_item_exists)

        # Check DB has updated correctly
        db_item = Item.objects.get(cex_id=self.existing_item.cex_id)
        self.assertEqual(db_item.title, update_item_data["boxName"])
        self.assertEqual(db_item.sell_price, update_item_data["sellPrice"])
        self.assertEqual(db_item.exchange_price, update_item_data["exchangePrice"])
        self.assertEqual(db_item.cash_price, update_item_data["cashPrice"])

        db_user_item_exists = UserItem.objects.filter(
            user=self.user, item=db_item
        ).exists()
        self.assertTrue(db_user_item_exists)

    def test_update_item_invalid_id(self):
        update_item_data = {
            "boxId": "-1",  # Invalid ID
            "boxName": "Updated Title",
            "sellPrice": 20.0,
            "exchangePrice": 12.50,
            "cashPrice": 10.0,
        }

        updated_item = cex.create_or_update_item(update_item_data, user=self.user)

        self.assertIsNone(updated_item)

        # Verify existing item remains unchanged
        db_item = Item.objects.get(cex_id=self.existing_item.cex_id)
        self.assertEqual(db_item.title, self.existing_item.title)
        self.assertEqual(db_item.sell_price, self.existing_item.sell_price)
        self.assertEqual(db_item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(db_item.cash_price, self.existing_item.cash_price)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_update_item_missing_attributes(self):
        update_item_data = {
            "boxId": self.existing_item.cex_id,
            "boxName": "Updated Title",
            "sellPrice": 20.0,
            # Missing - "exchangePrice": 12.50,
            # Missing - "cashPrice": 10.0
        }

        updated_item = cex.create_or_update_item(update_item_data, user=self.user)

        self.assertIsNone(updated_item)

        # Check DB has remains unchanged
        db_item = Item.objects.get(cex_id=self.existing_item.cex_id)
        self.assertEqual(db_item.title, self.existing_item.title)
        self.assertEqual(db_item.sell_price, self.existing_item.sell_price)
        self.assertEqual(db_item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(db_item.cash_price, self.existing_item.cash_price)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_create_or_update_item_none_input(self):
        item = cex.create_or_update_item(None, user=None)

        self.assertIsNone(item)

    @patch("items.models.db_models.Item.objects.get_or_create")
    def test_create_or_update_item_database_error(self, mock_get_or_create):
        mock_get_or_create.side_effect = DatabaseError
        item = cex.create_or_update_item(self.valid_fetched_item_data, self.user)

        self.assertIsNone(item)

    @patch("items.models.db_models.Item.objects.get_or_create")
    def test_create_or_update_item_unexpected_error(self, mock_get_or_create):
        mock_get_or_create.side_effect = Exception
        item = cex.create_or_update_item(self.valid_fetched_item_data, self.user)

        self.assertIsNone(item)

    def test_create_or_update_item_one_item_multiple_users(self):
        user_two = get_user_model().objects.create_user(
            username="user2", password="testpass2"
        )

        same_as_existing_item = {
            "boxId": self.existing_item.cex_id,
            "boxName": self.existing_item.title,
            "sellPrice": self.existing_item.sell_price,
            "exchangePrice": self.existing_item.exchange_price,
            "cashPrice": self.existing_item.cash_price,
        }

        # self.user already has self.existing_item
        item = cex.create_or_update_item(same_as_existing_item, user_two)

        self.assertIsNotNone(item)
        self.assertEqual(item.cex_id, self.existing_item.cex_id)
        self.assertEqual(item.title, self.existing_item.title)
        self.assertEqual(item.sell_price, self.existing_item.sell_price)
        self.assertEqual(item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(item.cash_price, self.existing_item.cash_price)

        user_one_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_one_item_exists)

        user_two_item_exists = UserItem.objects.filter(
            user=user_two, item=self.existing_item
        ).exists()
        self.assertTrue(user_two_item_exists)


class TestCexServiceDeleteItem(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )

        self.existing_item = Item.objects.create(
            cex_id="5060020626449",
            title="Halloween (18) 1978",
            sell_price=8.0,
            exchange_price=5.0,
            cash_price=3.0,
            last_checked=date(2025, 1, 1),
        )

        self.user_existing_item = UserItem.objects.get_or_create(
            user=self.user,
            item=self.existing_item,
        )

        self.valid_fetched_item_data = {
            "boxId": "5050582577013",
            "boxName": "Thing, The (18) 1982",
            "sellPrice": 6.0,
            "exchangePrice": 2.0,
            "cashPrice": 1.5,
        }

    def test_delete_item_success(self):
        user_item_already_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_already_exists)

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertTrue(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertFalse(user_item_exists)

    def test_delete_item_id_is_none(self):
        item_deleted = cex.delete_item(None, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_delete_item_invalid_id(self):
        item_deleted = cex.delete_item("-1", self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_delete_item_invalid_user(self):
        item_deleted = cex.delete_item(self.existing_item.cex_id, "invalid_user")

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    @patch("items.models.db_models.Item.objects.get")
    def test_delete_item_item_is_none(self, mock_get):
        mock_get.side_effect = None

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_delete_item_no_useritem_relation(self):
        UserItem.objects.filter(user=self.user, item=self.existing_item).delete()

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertFalse(user_item_exists)

    @patch("items.models.db_models.UserItem.delete")
    def test_delete_item_deleted_count_eq_0(self, mock_delete):
        mock_delete.return_value = (0, None)

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    @patch("items.models.db_models.UserItem.delete")
    def test_delete_item_deleted_count_gt_1(self, mock_delete):
        mock_delete.return_value = (3, None)

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    def test_delete_item_multiple_users(self):
        user_1 = get_user_model().objects.create(username="user1", password="pass1")
        user_2 = get_user_model().objects.create(username="user2", password="pass2")

        UserItem.objects.create(user=user_1, item=self.existing_item)
        UserItem.objects.create(user=user_2, item=self.existing_item)

        item_deleted = cex.delete_item(self.existing_item.cex_id, user_1)

        self.assertTrue(item_deleted)

        user_item_1_exists = UserItem.objects.filter(
            user=user_1, item=self.existing_item
        ).exists()
        user_item_2_exists = UserItem.objects.filter(
            user=user_2, item=self.existing_item
        ).exists()

        # User 1 doesn't have item but User 2 still does
        self.assertFalse(user_item_1_exists)
        self.assertTrue(user_item_2_exists)

    @patch("items.models.db_models.Item.objects.get")
    def test_delete_item_database_error(self, mock_get):
        mock_get.side_effect = DatabaseError

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)

    @patch("items.models.db_models.Item.objects.get")
    def test_delete_item_unknown_exception(self, mock_get):
        mock_get.side_effect = Exception

        item_deleted = cex.delete_item(self.existing_item.cex_id, self.user)

        self.assertFalse(item_deleted)

        user_item_exists = UserItem.objects.filter(
            user=self.user, item=self.existing_item
        ).exists()
        self.assertTrue(user_item_exists)


class TestCexServiceCreatePriceHistoryEntry(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )

        self.existing_item = Item.objects.create(
            cex_id="5060020626449",
            title="Halloween (18) 1978",
            sell_price=8.0,
            exchange_price=5.0,
            cash_price=3.0,
            last_checked=date(2025, 1, 1),
        )

        self.user_existing_item = UserItem.objects.get_or_create(
            user=self.user,
            item=self.existing_item,
        )

    def test_create_price_history_entry_success(self):
        price_entry = cex.create_price_history_entry(self.existing_item)

        self.assertEqual(price_entry.item.cex_id, self.existing_item.cex_id)
        self.assertEqual(price_entry.sell_price, self.existing_item.sell_price)
        self.assertEqual(price_entry.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(price_entry.cash_price, self.existing_item.cash_price)

    def test_create_price_history_entry_falsey_input(self):
        price_entry = cex.create_price_history_entry(None)

        self.assertIsNone(price_entry)

    def test_create_price_history_entry_invalid_item(self):
        invalid_object = {"one": 1, "two": 2}

        price_entry = cex.create_price_history_entry(invalid_object)

        self.assertIsNone(price_entry)

    @patch("items.models.db_models.PriceHistory.objects.create")
    def test_create_price_history_entry_database_error(self, mock_create):
        mock_create.side_effect = DatabaseError

        price_entry = cex.create_price_history_entry(self.existing_item)

        self.assertIsNone(price_entry)

    @patch("items.models.db_models.PriceHistory.objects.create")
    def test_create_price_history_entry_unexpected_error(self, mock_create):
        mock_create.side_effect = Exception

        price_entry = cex.create_price_history_entry(self.existing_item)

        self.assertIsNone(price_entry)


class TestCexServiceCreateOrUpdateItemAndPriceHistory(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )

        self.existing_item_fetched_data = {
            "boxId": "5060020626449",
            "boxName": "Halloween (18) 1978",
            "sellPrice": 8.0,
            "exchangePrice": 5.0,
            "cashPrice": 3.0,
        }

        self.existing_item = Item.objects.create(
            cex_id="5060020626449",
            title="Halloween (18) 1978",
            sell_price=8.0,
            exchange_price=5.0,
            cash_price=3.0,
            last_checked=date(2025, 1, 1),
        )

        self.user_existing_item = UserItem.objects.get_or_create(
            user=self.user,
            item=self.existing_item,
        )

        self.valid_fetched_item_data = {
            "boxId": "5050582577013",
            "boxName": "Thing, The (18) 1982",
            "sellPrice": 6.0,
            "exchangePrice": 2.0,
            "cashPrice": 1.5,
        }

    def test_create_or_update_item_and_price_history_invalid_item_data(self):
        invalid_item_data = {"invalid": "data"}

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            invalid_item_data, self.user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)

    def test_create_or_update_item_and_price_history_item_is_none(self):
        item, price_history_entry = cex.create_or_update_item_and_price_history(
            None, self.user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)

    def test_create_or_update_item_and_price_history_invalid_user(self):
        invalid_user = "invalid_user"

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.valid_fetched_item_data, invalid_user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)

    def test_create_or_update_item_and_price_history_no_price_history(self):
        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.valid_fetched_item_data, self.user
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.cex_id, self.valid_fetched_item_data["boxId"])
        self.assertEqual(item.title, self.valid_fetched_item_data["boxName"])
        self.assertEqual(item.sell_price, self.valid_fetched_item_data["sellPrice"])
        self.assertEqual(
            item.exchange_price, self.valid_fetched_item_data["exchangePrice"]
        )
        self.assertEqual(item.cash_price, self.valid_fetched_item_data["cashPrice"])

        self.assertIsNotNone(price_history_entry)
        self.assertEqual(price_history_entry.item, item)
        self.assertEqual(
            price_history_entry.sell_price, self.valid_fetched_item_data["sellPrice"]
        )
        self.assertEqual(
            price_history_entry.exchange_price,
            self.valid_fetched_item_data["exchangePrice"],
        )
        self.assertEqual(
            price_history_entry.cash_price, self.valid_fetched_item_data["cashPrice"]
        )

        self.assertEqual(PriceHistory.objects.count(), 1)

    def test_create_or_update_item_and_price_history_existing_price_history_change(
        self,
    ):
        PriceHistory.objects.create(
            item=self.existing_item,
            sell_price=1.0,
            exchange_price=1.0,
            cash_price=1.0,
            date_checked=date(2025, 1, 1),
        )

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.existing_item_fetched_data, self.user
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.cex_id, self.existing_item.cex_id)
        self.assertEqual(item.title, self.existing_item.title)
        self.assertEqual(item.sell_price, self.existing_item.sell_price)
        self.assertEqual(item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(item.cash_price, self.existing_item.cash_price)

        self.assertIsNotNone(price_history_entry)
        self.assertEqual(price_history_entry.item, item)
        self.assertEqual(price_history_entry.sell_price, self.existing_item.sell_price)
        self.assertEqual(
            price_history_entry.exchange_price, self.existing_item.exchange_price
        )
        self.assertEqual(price_history_entry.cash_price, self.existing_item.cash_price)

        self.assertEqual(PriceHistory.objects.count(), 2)

    def test_create_or_update_item_and_price_history_existing_price_history_no_change(
        self,
    ):
        PriceHistory.objects.create(
            item=self.existing_item,
            sell_price=self.existing_item.sell_price,
            exchange_price=self.existing_item.exchange_price,
            cash_price=self.existing_item.cash_price,
            date_checked=date(2025, 1, 1),
        )

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.existing_item_fetched_data, self.user
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.cex_id, self.existing_item.cex_id)
        self.assertEqual(item.title, self.existing_item.title)
        self.assertEqual(item.sell_price, self.existing_item.sell_price)
        self.assertEqual(item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(item.cash_price, self.existing_item.cash_price)

        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 1)

    @patch("items.models.db_models.Item.objects.get_or_create")
    def test_create_or_update_item_and_price_history_failed_to_create_item(
        self, mock_get_or_create
    ):
        mock_get_or_create.return_value = None

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.valid_fetched_item_data, self.user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)

    @patch("items.models.db_models.PriceHistory.objects.create")
    def test_create_or_update_item_and_price_history_failed_to_create_price_history(
        self, mock_create
    ):
        mock_create.return_value = None

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.valid_fetched_item_data, self.user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)

    @patch("items.services.cex.create_or_update_item")
    def test_create_or_update_item_and_price_history_database_error(self, mock_call):
        mock_call.side_effect = DatabaseError

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.valid_fetched_item_data, self.user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)

    @patch("items.services.cex.create_or_update_item")
    def test_create_or_update_item_and_price_history_unknown_exception(self, mock_call):
        mock_call.side_effect = Exception

        item, price_history_entry = cex.create_or_update_item_and_price_history(
            self.valid_fetched_item_data, self.user
        )

        self.assertIsNone(item)
        self.assertIsNone(price_history_entry)

        self.assertEqual(PriceHistory.objects.count(), 0)


class TestCexServiceCheckPriceUpdates(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )

        self.item_with_valid_cex_id = Item.objects.create(
            cex_id="123456",
            title="Valid Item",
            sell_price=20.0,
            exchange_price=15.0,
            cash_price=10.0,
            last_checked=date(2024, 12, 31),
        )

        self.user_existing_item = UserItem.objects.get_or_create(
            user=self.user,
            item=self.item_with_valid_cex_id,
        )

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_single_item(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": 15.0,
                            "exchangePrice": 3.0,
                            "cashPrice": 8.0,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, 15.0)
        self.assertEqual(updated_item.exchange_price, 3.0)
        self.assertEqual(updated_item.cash_price, 8.0)

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, 15.0)
        self.assertEqual(updated_item.exchange_price, 3.0)
        self.assertEqual(updated_item.cash_price, 8.0)

    @pytest.mark.skip(reason="Test not implemented")
    def test_check_price_updates_multiple_items(self):
        self.assertIsNotNone(None)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_no_price_change(self, mock_get):
        current_sell_price = self.item_with_valid_cex_id.sell_price
        current_exchange_price = self.item_with_valid_cex_id.exchange_price
        current_cash_price = self.item_with_valid_cex_id.cash_price

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": current_sell_price,
                            "exchangePrice": current_exchange_price,
                            "cashPrice": current_cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 0)

        # Check DB
        self.item_with_valid_cex_id.refresh_from_db()
        self.assertEqual(self.item_with_valid_cex_id.sell_price, current_sell_price)
        self.assertEqual(
            self.item_with_valid_cex_id.exchange_price, current_exchange_price
        )
        self.assertEqual(self.item_with_valid_cex_id.cash_price, current_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_cash_price_increases(self, mock_get):
        increased_cash_price = max(self.item_with_valid_cex_id.cash_price + 10.5, 0)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": self.item_with_valid_cex_id.sell_price,
                            "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                            "cashPrice": increased_cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(updated_item.cash_price, increased_cash_price)

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(updated_item.cash_price, increased_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_cash_price_decreases(self, mock_get):
        decreased_cash_price = max(self.item_with_valid_cex_id.cash_price - 1, 0)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": self.item_with_valid_cex_id.sell_price,
                            "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                            "cashPrice": decreased_cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(updated_item.cash_price, decreased_cash_price)

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(updated_item.cash_price, decreased_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_sell_price_increases(self, mock_get):
        increased_sell_price = max(self.item_with_valid_cex_id.sell_price + 10.5, 0)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": increased_sell_price,
                            "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                            "cashPrice": self.item_with_valid_cex_id.cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, increased_sell_price)
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, increased_sell_price)
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_sell_price_decreases(self, mock_get):
        decreased_sell_price = max(self.item_with_valid_cex_id.sell_price - 1, 0)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": decreased_sell_price,
                            "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                            "cashPrice": self.item_with_valid_cex_id.cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, decreased_sell_price)
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, decreased_sell_price)
        self.assertEqual(
            updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price
        )
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_exchange_price_increases(self, mock_get):
        increased_exchange_price = max(
            self.item_with_valid_cex_id.exchange_price + 10.5, 0
        )

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": self.item_with_valid_cex_id.sell_price,
                            "exchangePrice": increased_exchange_price,
                            "cashPrice": self.item_with_valid_cex_id.cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(updated_item.exchange_price, increased_exchange_price)
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(updated_item.exchange_price, increased_exchange_price)
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_exchange_price_decreases(self, mock_get):
        decreased_exchange_price = max(
            self.item_with_valid_cex_id.exchange_price - 1, 0
        )

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": self.item_with_valid_cex_id.sell_price,
                            "exchangePrice": decreased_exchange_price,
                            "cashPrice": self.item_with_valid_cex_id.cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(updated_item.exchange_price, decreased_exchange_price)
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(
            updated_item.sell_price, self.item_with_valid_cex_id.sell_price
        )
        self.assertEqual(updated_item.exchange_price, decreased_exchange_price)
        self.assertEqual(
            updated_item.cash_price, self.item_with_valid_cex_id.cash_price
        )

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_all_prices_increase(self, mock_get):
        increased_sell_price = max(self.item_with_valid_cex_id.sell_price + 1, 0)
        increased_exchange_price = max(
            self.item_with_valid_cex_id.exchange_price + 2, 0
        )
        increased_cash_price = max(self.item_with_valid_cex_id.cash_price + 3, 0)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": increased_sell_price,
                            "exchangePrice": increased_exchange_price,
                            "cashPrice": increased_cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, increased_sell_price)
        self.assertEqual(updated_item.exchange_price, increased_exchange_price)
        self.assertEqual(updated_item.cash_price, increased_cash_price)

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, increased_sell_price)
        self.assertEqual(updated_item.exchange_price, increased_exchange_price)
        self.assertEqual(updated_item.cash_price, increased_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_all_prices_decreases(self, mock_get):
        decreased_sell_price = max(self.item_with_valid_cex_id.sell_price - 1, 0)
        decreased_exchange_price = max(
            self.item_with_valid_cex_id.exchange_price - 2, 0
        )
        decreased_cash_price = max(self.item_with_valid_cex_id.cash_price - 3, 0)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": decreased_sell_price,
                            "exchangePrice": decreased_exchange_price,
                            "cashPrice": decreased_cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)

        updated_item = updated_items[0]

        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, decreased_sell_price)
        self.assertEqual(updated_item.exchange_price, decreased_exchange_price)
        self.assertEqual(updated_item.cash_price, decreased_cash_price)

        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, decreased_sell_price)
        self.assertEqual(updated_item.exchange_price, decreased_exchange_price)
        self.assertEqual(updated_item.cash_price, decreased_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_all_prices_negative(self, mock_get):
        negative_sell_price = -1.0
        negative_exchange_price = -1.0
        negative_cash_price = -1.0

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            "boxName": self.item_with_valid_cex_id.title,
                            "sellPrice": negative_sell_price,
                            "exchangePrice": negative_exchange_price,
                            "cashPrice": negative_cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 0)

        # DB Check
        self.item_with_valid_cex_id.refresh_from_db()
        self.assertEqual(
            self.item_with_valid_cex_id.cex_id, self.item_with_valid_cex_id.cex_id
        )
        self.assertEqual(
            self.item_with_valid_cex_id.title, self.item_with_valid_cex_id.title
        )
        self.assertNotEqual(self.item_with_valid_cex_id.sell_price, negative_sell_price)
        self.assertNotEqual(
            self.item_with_valid_cex_id.exchange_price, negative_exchange_price
        )
        self.assertNotEqual(self.item_with_valid_cex_id.cash_price, negative_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_no_items_to_check(self, mock_get):
        Item.objects.all().delete()

        updated_items = cex.check_price_updates()

        self.assertEqual(len(updated_items), 0)

        mock_get.assert_not_called()

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_incorrect_format(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "ack": "success",
                "data": {
                    "boxDetails": [
                        {
                            "boxId": self.item_with_valid_cex_id.cex_id,
                            # Missing - "boxName": self.item_with_valid_cex_id.title,
                            # Missing - "sellPrice": self.item_with_valid_cex_id.sell_price,
                            "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                            "cashPrice": self.item_with_valid_cex_id.cash_price,
                        }
                    ]
                },
                "error": {"code": "", "internal_message": "", "moreInfo": []},
            }
        }

        updated_items = cex.check_price_updates()

        # Invalid Items are skipped
        self.assertEqual(len(updated_items), 0)

    @patch("items.services.cex.fetch_item")
    def test_check_price_updates_http_error(self, mock_fetch_item):
        mock_fetch_item.side_effect = requests.exceptions.HTTPError

        updated_items = cex.check_price_updates()

        self.assertIsNone(updated_items)

    @patch("items.services.cex.fetch_item")
    def test_check_price_updates_json_error(self, mock_fetch_item):
        mock_fetch_item.side_effect = requests.exceptions.JSONDecodeError

        updated_items = cex.check_price_updates()

        self.assertIsNone(updated_items)

    @patch("items.services.cex.fetch_item")
    def test_check_price_updates_unexpected_error(self, mock_fetch_item):
        mock_fetch_item.side_effect = Exception

        updated_items = cex.check_price_updates()

        self.assertIsNone(updated_items)
