from abc import ABC
import logging
from typing import Optional

from pydantic import ValidationError

from items.models.pydantic_models import ItemData

logger = logging.getLogger(__name__)


class ItemDataValidator(ABC):
    def validate_item_data(self, item_data) -> Optional[ItemData]:
        if item_data is None:
            logger.error("Item data is None, cannot validate item")
            return None

        try:
            validated_item_data = ItemData.model_validate(item_data)
            # TODO: Validate box_id using regex before
            return validated_item_data
        except ValidationError as e:
            logger.exception("Error validating item data", e)
            return None
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return None
