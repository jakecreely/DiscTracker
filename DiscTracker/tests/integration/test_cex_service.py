import pytest
import requests
from unittest.mock import patch
from items.services.cex_service import CexService


@pytest.fixture
def cex_service():
    return CexService()


@patch("items.services.cex_service.requests.get")
def test_fetch_item_success(mock_get, cex_service):
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

    item = cex_service.fetch_item("711719417576")

    assert item is not None
    assert item.cex_id == "711719417576"
    assert item.title == "Spider-Man (2018) No DLC"
    assert item.sell_price == 15.0
    assert item.exchange_price == 10.0
    assert item.cash_price == 7.0


@patch("items.services.cex_service.requests.get")
def test_fetch_item_invalid_cex_id(mock_get, cex_service):
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
    item = cex_service.fetch_item(invalid_cex_id)

    assert item is None


@patch("items.services.cex_service.requests.get")
def test_fetch_item_invalid_response_schema(mock_get, cex_service):
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

    item = cex_service.fetch_item("711719417576")

    assert item is None


@patch("items.services.cex_service.requests.get")
def test_fetch_item_additional_attributes(mock_get, cex_service):
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

    item = cex_service.fetch_item("711719417576")

    assert item is not None
    assert item.cex_id == "711719417576"
    assert item.title == "Spider-Man (2018) No DLC"
    assert item.sell_price == 15.0
    assert item.exchange_price == 10.0
    assert item.cash_price == 7.0
    assert "extraField" not in item


@patch("items.services.cex_service.requests.get")
def test_fetch_item_http_error(mock_get, cex_service):
    mock_get.return_value.status_code = 404
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError

    item = cex_service.fetch_item("711719417576")

    assert item is None


@patch("items.services.cex_service.requests.get")
def test_fetch_item_json_error(mock_get, cex_service):
    mock_get.return_value.status_code = 404
    mock_get.return_value.raise_for_status.side_effect = (
        requests.exceptions.JSONDecodeError("", "", 0)
    )

    item = cex_service.fetch_item("711719417576")

    assert item is None


@patch("items.services.cex_service.requests.get")
def test_fetch_item_unexpected_error(mock_get, cex_service):
    mock_get.return_value.status_code = 404
    mock_get.return_value.raise_for_status.side_effect = Exception

    item = cex_service.fetch_item("711719417576")

    assert item is None
