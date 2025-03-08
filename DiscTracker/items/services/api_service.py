from typing import Optional
import requests
import logging
from pydantic import ValidationError

from items.models.pydantic_models import (
    CexItemApiResponseWrapper,
    CexIdValidator,
    ItemData,
)

logger = logging.getLogger(__name__)

CEX_API_BASE_URL = "https://wss2.cex.uk.webuy.io/v3/boxes"


class CexService:
    def __init__(self):
        pass

    def fetch_item(self, cex_id) -> Optional[ItemData]:
        if not self._validate_cex_id(cex_id):
            logger.error("CEX ID validation failed")
            return None

        try:
            response_json = self._get_item_data(cex_id)
            validated_response = self._validate_response(response_json)

            if not validated_response:
                logger.error(f"Response validation failed for {cex_id}")
                return None

            logger.info("Successfully fetched item with CEX ID %s", cex_id)

            api_data = validated_response.response.data.boxDetails
            item_data = ItemData.from_api(api_data)

            return item_data
        except requests.exceptions.HTTPError as e:
            logger.exception(
                "HTTP Error when fetching item by CEX ID %s: %s", cex_id, e
            )
            return None
        except requests.exceptions.JSONDecodeError as e:
            logger.exception(
                "Failed to parse JSON response for CEX ID %s: %s", cex_id, e
            )
            return None
        except Exception as e:
            logger.exception(
                "An unexpected error occurred for fetching item by CEX ID %s: %s",
                cex_id,
                e,
            )
            return None

    def _get_item_data(self, cex_id) -> Optional[dict]:
        search_url = f"{CEX_API_BASE_URL}/{cex_id}/detail"

        try:
            response = requests.get(search_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.exception(
                "HTTP Error when fetching item by CEX ID %s: %s", cex_id, e
            )
            return None
        except requests.exceptions.JSONDecodeError as e:
            logger.exception(
                "Failed to parse JSON response for CEX ID %s: %s", cex_id, e
            )
            return None
        except Exception as e:
            logger.exception(
                "An unexpected error occurred for fetching item by CEX ID %s: %s",
                cex_id,
                e,
            )
            return None

    def _validate_response(
        self, response_json: dict
    ) -> Optional[CexItemApiResponseWrapper]:
        try:
            return CexItemApiResponseWrapper.model_validate(response_json)
        except ValidationError as e:
            logger.exception(f"Error validating CEX ID: {e}")
            return None

    def _validate_cex_id(self, cex_id) -> bool:
        if not cex_id:
            logger.error(f"CEX ID not provided: {cex_id}")
            return False

        try:
            CexIdValidator(cex_id=cex_id)
            return True
        except ValidationError as e:
            logger.exception(f"Error validating CEX ID: {e}")
            return False
