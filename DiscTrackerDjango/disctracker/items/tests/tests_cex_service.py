import requests
from datetime import datetime
from django.test import TestCase
from django.db import DatabaseError
from unittest.mock import patch
from items.services import cex
from items.models import Item

class TestCexServiceFetchItem(TestCase):
    @patch('items.services.cex.requests.get')
    def test_fetch_item_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": "711719417576",
                        "boxName": "Spider-Man (2018) No DLC",
                        "sellPrice": 15.0,
                        "exchangePrice": 10.0,
                        "cashPrice": 7.0
                    }]
                }
            }
        }
        
        result = cex.fetch_item("711719417576")

        self.assertIsNotNone(result)
        self.assertEqual(result["boxDetails"][0]["boxId"], "711719417576")
        self.assertEqual(result["boxDetails"][0]["boxName"], "Spider-Man (2018) No DLC")
        self.assertEqual(result["boxDetails"][0]["sellPrice"], 15.0)
        self.assertEqual(result["boxDetails"][0]["exchangePrice"], 10.0)
        self.assertEqual(result["boxDetails"][0]["cashPrice"], 7.0)

    @patch('items.services.cex.requests.get')
    def test_fetch_item_invalid_cex_id(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.json.return_value = {
            "response": {
                "data": "",
                "error": {
                    "code": 12,
                    "internal_message": "Service not found",
                    "moreInfo": []
                }
            }
        }
        
        invalid_cex_id = "-1"
        result = cex.fetch_item(invalid_cex_id)

        self.assertIsNone(result)
    
    @patch('items.services.cex.requests.get')
    def test_fetch_item_http_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
        
        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)
        
    @patch('items.services.cex.requests.get')
    def test_fetch_item_json_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.JSONDecodeError("", "", 0)
        
        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)
        
    @patch('items.services.cex.requests.get')
    def test_fetch_item_unexpected_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = Exception
        
        result = cex.fetch_item("711719417576")

        self.assertIsNone(result)
        
class TestCexServiceCreateOrUpdateItem(TestCase):
    
    def setUp(self):
        self.existing_item = Item.objects.create(
            cex_id="5060020626449",
            title="Halloween (18) 1978",
            sell_price=8.0,
            exchange_price=5.0,
            cash_price=3.0,
            last_checked=datetime(2025, 1, 1)
        )

        self.valid_fetched_item_data = {
            "boxDetails": [
                {
                    "boxId": "5050582577013",
                    "boxName": "Thing, The (18) 1982",
                    "sellPrice": 6.0,
                    "exchangePrice": 2.0,
                    "cashPrice": 1.5
                }
            ]
        }
        
    def test_create_item_success(self):
        created_item = cex.create_or_update_item(self.valid_fetched_item_data)
        
        self.assertIsNotNone(created_item)
        self.assertEqual(created_item.cex_id, self.valid_fetched_item_data["boxDetails"][0]["boxId"])
        self.assertEqual(created_item.title, self.valid_fetched_item_data["boxDetails"][0]["boxName"])
        self.assertEqual(created_item.sell_price, self.valid_fetched_item_data["boxDetails"][0]["sellPrice"])
        self.assertEqual(created_item.exchange_price, self.valid_fetched_item_data["boxDetails"][0]["exchangePrice"])
        self.assertEqual(created_item.cash_price, self.valid_fetched_item_data["boxDetails"][0]["cashPrice"])
    
    def test_create_item_invalid_id(self):
        invalid_fetched_item_data = {
            "boxDetails": [{
                "boxId": "-1", # Invalid ID
                "boxName": "Thing, The (18) 1982",
                "sellPrice": 6.0,
                "exchangePrice": 2.0,
                "cashPrice": 1.5
            }]
        }
        
        created_item = cex.create_or_update_item(invalid_fetched_item_data)
        
        self.assertIsNone(created_item)
    
    def test_create_item_missing_attributes(self):
        fetched_item_data = {
            "boxDetails": [{
                "boxId": "5050582577013",
                "exchangePrice": 2.0,
                "cashPrice": 1.5
            }]
        }
        
        created_item = cex.create_or_update_item(fetched_item_data)
        
        self.assertIsNone(created_item)
    
    def test_update_item_success(self):
        update_item_data = {
            "boxDetails": [
                {
                    "boxId": self.existing_item.cex_id,
                    "boxName": "Updated Title",
                    "sellPrice": 20.0,
                    "exchangePrice": 12.50,
                    "cashPrice": 10.0
                }
            ]
        }
        
        updated_item = cex.create_or_update_item(update_item_data)
        
        self.assertIsNotNone(updated_item)
        self.assertEqual(updated_item.cex_id, self.existing_item.cex_id) # ID remains the same
        self.assertEqual(updated_item.title, update_item_data["boxDetails"][0]["boxName"])
        self.assertEqual(updated_item.sell_price, update_item_data["boxDetails"][0]["sellPrice"])
        self.assertEqual(updated_item.exchange_price, update_item_data["boxDetails"][0]["exchangePrice"])
        self.assertEqual(updated_item.cash_price, update_item_data["boxDetails"][0]["cashPrice"])

        # Check DB has updated correctly        
        db_item = Item.objects.get(cex_id=self.existing_item.cex_id)
        self.assertEqual(db_item.title, update_item_data["boxDetails"][0]["boxName"])
        self.assertEqual(db_item.sell_price, update_item_data["boxDetails"][0]["sellPrice"])
        self.assertEqual(db_item.exchange_price, update_item_data["boxDetails"][0]["exchangePrice"])
        self.assertEqual(db_item.cash_price, update_item_data["boxDetails"][0]["cashPrice"])
        
    def test_update_item_invalid_id(self):
        update_item_data = {
            "boxDetails": [
                {
                    "boxId": '-1', # Invalid ID
                    "boxName": "Updated Title",
                    "sellPrice": 20.0,
                    "exchangePrice": 12.50,
                    "cashPrice": 10.0
                }
            ]
        }
        
        updated_item = cex.create_or_update_item(update_item_data)
        
        self.assertIsNone(updated_item)
    
        # Verify existing item remains unchanged
        db_item = Item.objects.get(cex_id=self.existing_item.cex_id)
        self.assertEqual(db_item.title, self.existing_item.title)
        self.assertEqual(db_item.sell_price, self.existing_item.sell_price)
        self.assertEqual(db_item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(db_item.cash_price, self.existing_item.cash_price)
    

    def test_update_item_missing_attributes(self):
        update_item_data = {
            "boxDetails": [
                {
                    "boxId": self.existing_item.cex_id,
                    "boxName": "Updated Title",
                    "sellPrice": 20.0
                    # Missing - "exchangePrice": 12.50,
                    # Missing - "cashPrice": 10.0
                }
            ]
        }
        
        updated_item = cex.create_or_update_item(update_item_data)
        
        self.assertIsNotNone(updated_item)
        self.assertEqual(updated_item.cex_id, self.existing_item.cex_id) # ID remains the same
        self.assertEqual(updated_item.title, update_item_data["boxDetails"][0]["boxName"])
        self.assertEqual(updated_item.sell_price, update_item_data["boxDetails"][0]["sellPrice"])
        self.assertEqual(updated_item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(updated_item.cash_price, self.existing_item.cash_price)
        
        # Check DB has updated correctly        
        db_item = Item.objects.get(cex_id=self.existing_item.cex_id)
        self.assertEqual(db_item.title, update_item_data["boxDetails"][0]["boxName"])
        self.assertEqual(db_item.sell_price, update_item_data["boxDetails"][0]["sellPrice"])
        self.assertEqual(db_item.exchange_price, self.existing_item.exchange_price)
        self.assertEqual(db_item.cash_price, self.existing_item.cash_price)
    
    def test_create_or_update_item_none_input(self):
        item = cex.create_or_update_item(None)
        
        self.assertIsNone(item)
    
    @patch("items.models.Item.objects.get_or_create")
    def test_create_or_update_item_database_error(self, mock_get_or_create):
        mock_get_or_create.side_effect = DatabaseError
        item = cex.create_or_update_item(self.valid_fetched_item_data)
        
        self.assertIsNone(item)
    
    @patch("items.models.Item.objects.get_or_create")
    def test_create_or_update_item_unexpected_error(self, mock_get_or_create):
        mock_get_or_create.side_effect = Exception
        item = cex.create_or_update_item(self.valid_fetched_item_data)
        
        self.assertIsNone(item)
        
class TestCexServiceCreatePriceHistoryEntry(TestCase):
    def setUp(self):
        self.existing_item = Item.objects.create(
            cex_id="5060020626449",
            title="Halloween (18) 1978",
            sell_price=8.0,
            exchange_price=5.0,
            cash_price=3.0,
            last_checked=datetime(2025, 1, 1)
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
        invalid_object = {
            "one": 1,
            "two": 2
        }
        
        price_entry = cex.create_price_history_entry(invalid_object)
        
        self.assertIsNone(price_entry)
    
    @patch("items.models.PriceHistory.objects.create")
    def test_create_price_history_entry_database_error(self, mock_create):
        mock_create.side_effect = DatabaseError
        
        price_entry = cex.create_price_history_entry(self.existing_item)
        
        self.assertIsNone(price_entry)
        
    @patch("items.models.PriceHistory.objects.create")
    def test_create_price_history_entry_unexpected_error(self, mock_create):
        mock_create.side_effect = Exception
        
        price_entry = cex.create_price_history_entry(self.existing_item)
        
        self.assertIsNone(price_entry)
        
class TestCexServiceCheckPriceUpdates(TestCase):
    def setUp(self):
        self.item_with_valid_cex_id = Item.objects.create(
            cex_id="123456",
            title="Valid Item",
            sell_price=20.0,
            exchange_price=15.0,
            cash_price=10.0,
            last_checked=datetime(2024, 12, 31),
        )
        pass
    
    @patch('items.services.cex.requests.get')
    def test_check_price_updates_single_item(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": 15.0,
                        "exchangePrice": 3.0,
                        "cashPrice": 8.0
                    }]
                }
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
    
    
    def test_check_price_updates_multiple_items(self):
        self.assertIsNotNone(None)
    
    @patch('items.services.cex.requests.get')
    def test_check_price_updates_no_price_change(self, mock_get):
        current_sell_price = self.item_with_valid_cex_id.sell_price
        current_exchange_price = self.item_with_valid_cex_id.exchange_price
        current_cash_price = self.item_with_valid_cex_id.cash_price
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": current_sell_price,
                        "exchangePrice": current_exchange_price,
                        "cashPrice": current_cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 0)
        
        # Check DB
        self.item_with_valid_cex_id.refresh_from_db()
        self.assertEqual(self.item_with_valid_cex_id.sell_price, current_sell_price)
        self.assertEqual(self.item_with_valid_cex_id.exchange_price, current_exchange_price)
        self.assertEqual(self.item_with_valid_cex_id.cash_price, current_cash_price)

    @patch("items.services.cex.requests.get")
    def test_check_price_updates_cash_price_increases(self, mock_get):
        increased_cash_price = max(self.item_with_valid_cex_id.cash_price + 10.5, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": self.item_with_valid_cex_id.sell_price,
                        "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                        "cashPrice": increased_cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        updated_item = updated_items[0]
        
        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, increased_cash_price)
        
        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, increased_cash_price)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_cash_price_decreases(self, mock_get):
        decreased_cash_price = max(self.item_with_valid_cex_id.cash_price - 1, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": self.item_with_valid_cex_id.sell_price,
                        "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                        "cashPrice": decreased_cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        updated_item = updated_items[0]
        
        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, decreased_cash_price)
        
        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, decreased_cash_price)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_sell_price_increases(self, mock_get):
        increased_sell_price = max(self.item_with_valid_cex_id.sell_price + 10.5, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": increased_sell_price,
                        "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                        "cashPrice": self.item_with_valid_cex_id.cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        updated_item = updated_items[0]
        
        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, increased_sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
        
        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, increased_sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_sell_price_decreases(self, mock_get):
        decreased_sell_price = max(self.item_with_valid_cex_id.sell_price - 1, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": decreased_sell_price,
                        "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                        "cashPrice": self.item_with_valid_cex_id.cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        updated_item = updated_items[0]
        
        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, decreased_sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
        
        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, decreased_sell_price)
        self.assertEqual(updated_item.exchange_price, self.item_with_valid_cex_id.exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_exchange_price_increases(self, mock_get):
        increased_exchange_price = max(self.item_with_valid_cex_id.exchange_price + 10.5, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": self.item_with_valid_cex_id.sell_price,
                        "exchangePrice": increased_exchange_price,
                        "cashPrice": self.item_with_valid_cex_id.cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        updated_item = updated_items[0]
        
        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, increased_exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
        
        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, increased_exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_exchange_price_decreases(self, mock_get):
        decreased_exchange_price = max(self.item_with_valid_cex_id.exchange_price - 1, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": self.item_with_valid_cex_id.sell_price,
                        "exchangePrice": decreased_exchange_price,
                        "cashPrice": self.item_with_valid_cex_id.cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        updated_item = updated_items[0]
        
        # Check Response
        self.assertEqual(updated_item.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(updated_item.title, self.item_with_valid_cex_id.title)
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, decreased_exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
        
        # DB Check
        updated_item.refresh_from_db()
        self.assertEqual(updated_item.sell_price, self.item_with_valid_cex_id.sell_price)
        self.assertEqual(updated_item.exchange_price, decreased_exchange_price)
        self.assertEqual(updated_item.cash_price, self.item_with_valid_cex_id.cash_price)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_all_prices_increase(self, mock_get):
        increased_sell_price = max(self.item_with_valid_cex_id.sell_price + 1, 0)
        increased_exchange_price = max(self.item_with_valid_cex_id.exchange_price + 2, 0)
        increased_cash_price = max(self.item_with_valid_cex_id.cash_price + 3, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": increased_sell_price,
                        "exchangePrice": increased_exchange_price,
                        "cashPrice": increased_cash_price
                    }]
                }
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
        decreased_exchange_price = max(self.item_with_valid_cex_id.exchange_price - 2, 0)
        decreased_cash_price = max(self.item_with_valid_cex_id.cash_price - 3, 0)
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": decreased_sell_price,
                        "exchangePrice": decreased_exchange_price,
                        "cashPrice": decreased_cash_price
                    }]
                }
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
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        "boxName": self.item_with_valid_cex_id.title,
                        "sellPrice": negative_sell_price,
                        "exchangePrice": negative_exchange_price,
                        "cashPrice": negative_cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        self.assertEqual(len(updated_items), 1)
        
        # DB Check
        self.item_with_valid_cex_id.refresh_from_db()
        self.assertEqual(self.item_with_valid_cex_id.cex_id, self.item_with_valid_cex_id.cex_id)
        self.assertEqual(self.item_with_valid_cex_id.title, self.item_with_valid_cex_id.title)
        self.assertNotEqual(self.item_with_valid_cex_id.sell_price, negative_sell_price)
        self.assertNotEqual(self.item_with_valid_cex_id.exchange_price, negative_exchange_price)
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
                "data": {
                    "boxDetails": [{
                        "boxId": self.item_with_valid_cex_id.cex_id,
                        # Missing - "boxName": self.item_with_valid_cex_id.title,
                        # Missing - "sellPrice": self.item_with_valid_cex_id.sell_price,
                        "exchangePrice": self.item_with_valid_cex_id.exchange_price,
                        "cashPrice": self.item_with_valid_cex_id.cash_price
                    }]
                }
            }
        }
        
        updated_items = cex.check_price_updates()
        
        self.assertIsNone(updated_items)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_http_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.HTTPError
        
        updated_items = cex.check_price_updates()
        
        self.assertIsNone(updated_items)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_json_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.JSONDecodeError
        
        updated_items = cex.check_price_updates()
        
        self.assertIsNone(updated_items)
    
    @patch("items.services.cex.requests.get")
    def test_check_price_updates_unexpected_error(self, mock_get):
        mock_get.side_effect = Exception
        
        updated_items = cex.check_price_updates()
        
        self.assertIsNone(updated_items)