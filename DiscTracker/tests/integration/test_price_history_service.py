from datetime import date
from django.test import TestCase
from django.db import DatabaseError
from django.contrib.auth import get_user_model
from unittest.mock import patch
from items.services import cex
from items.models.db_models import Item, UserItem


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
