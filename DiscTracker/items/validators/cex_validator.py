import logging
from typing import Optional
from pydantic import ValidationError
from items.models.pydantic_models import CexApiItemDetail

logger = logging.getLogger(__name__)


class CexDataValidator:
    def validate_item_data(self, item_data) -> Optional[CexApiItemDetail]:
        if item_data is None:
            logger.error("Item data is None, cannot validate item")
            return None

        try:
            validated_item_data = CexApiItemDetail.model_validate(item_data)
            # TODO: Validate box_id using regex before
            return validated_item_data
        except ValidationError as e:
            logger.exception("Error validating item data", e)
            return None
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return None
