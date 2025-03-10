from datetime import date
import logging
from typing import Optional

from django.db import DatabaseError
from pydantic import ValidationError

from items.models.db_models import Item, PriceHistory

logger = logging.getLogger(__name__)


class PriceHistoryService:
    def __init__(self):
        pass

    def create_price_history_entry(self, item: Item) -> Optional[PriceHistory]:
        if not self._validate_item(item):
            logger.error("Item validation failed")
            return None

        try:
            price_entry = PriceHistory.objects.create(
                item=item,
                sell_price=item.sell_price,
                exchange_price=item.exchange_price,
                cash_price=item.cash_price,
                date_checked=date.today(),
            )
            logger.info(f"Created price history entry for item {item.cex_id}")
            return price_entry
        except DatabaseError as e:
            logger.exception(f"Database error while creating price history: {e}")
            return None
        except AttributeError as e:
            logger.exception(
                f"Missing attributes in item {item.cex_id} while creating price history: {e}"
            )
            return None
        except Exception as e:
            logger.exception(
                f"Failed to create price history entry for item {item.cex_id}: {e}"
            )
            return None

    def create_price_history_if_price_changed(self, item: Item):
        latest_price_history = (
            PriceHistory.objects.filter(item=item).order_by("-date_checked").first()
        )

        if not latest_price_history:
            logger.error(f"Failed to get latest price history for {item.cex_id}")
            return None

        if self.has_price_changed(
            item,
            latest_price_history.sell_price,
            latest_price_history.exchange_price,
            latest_price_history.cash_price,
        ):
            price_history_entry = self.create_price_history_entry(item)
            if price_history_entry is None:
                logger.error(
                    "Failed to create price history entry for item with CEX ID: %s",
                    item.cex_id,
                )
                raise None
            else:
                return price_history_entry
        else:
            return None

    # TODO: Change to equal method
    def has_price_changed(
        self, item: Item, new_sell_price, new_exchange_price, new_cash_price
    ) -> bool:
        return (
            item.sell_price != new_sell_price
            or item.exchange_price != new_exchange_price
            or item.cash_price != new_cash_price
        )

    def _validate_item(self, item: Item) -> bool:
        if not item:
            logger.error("Item is None, cannot validate")
            return False

        if not isinstance(item, Item):
            logger.error(
                f"Invalid item type, expected Item model instead of {type(item)}"
            )
            return False

        try:
            item.full_clean()
            return True
        except ValidationError as e:
            logger.error(f"Item validation failed: {e}")
            return False
