import requests
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