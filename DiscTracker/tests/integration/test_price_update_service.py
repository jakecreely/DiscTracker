import pytest
import requests
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from items.services import cex
from items.models.db_models import Item, UserItem


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
