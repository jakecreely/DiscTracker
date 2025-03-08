import requests
from django.test import TestCase
from unittest.mock import patch
from items.services import cex


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
