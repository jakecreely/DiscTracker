import logging

from django.db import DatabaseError, transaction
from items.services.price_history_service import PriceHistoryService
from items.services.api_service import CexService
from items.services.item_service import ItemService

logger = logging.getLogger(__name__)


class PriceUpdateService:
    def __init__(
        self,
        item_service: ItemService,
        api_service: CexService,
        price_history_service: PriceHistoryService,
    ):
        self.item_service = item_service
        self.price_history_service = price_history_service
        self.api_service = api_service

    def check_price_updates(self):
        updated_items = []

        try:
            logger.info("Starting price update check.")
            items = self.item_service.get_all_items()

            for item in items:
                if not item.cex_id:
                    logger.warning("Item has no cex_id so skipping")
                    continue

                logger.info(f"Fetching data for CEX ID: {item.cex_id}")

                fetched_item_data = self.api_service.fetch_item(item.cex_id)

                if not fetched_item_data:
                    logger.warning(
                        f"No fetched data for CEX ID {item.cex_id} so skipping"
                    )
                    continue

                if not self._validate_price_data(fetched_item_data):
                    logger.warning(f"Invalid price data for CEX ID: {item.cex_id}")
                    continue

                if self.price_history_service.has_price_changed(
                    item,
                    fetched_item_data.sell_price,
                    fetched_item_data.exchange_price,
                    fetched_item_data.cash_price,
                ):
                    try:
                        with transaction.atomic():
                            updated_item = self.item_service.update_item(
                                fetched_item_data
                            )
                            if not item:
                                raise DatabaseError(
                                    f"Failed to update item for CEX ID {item.cex_id}"
                                )
                            price_history_entry = (
                                self.price_history_service.create_price_history_entry(
                                    item, updated_item
                                )
                            )
                            if not price_history_entry:
                                raise DatabaseError(
                                    f"Failed to create price history entry for CEX ID {item.cex_id}"
                                )
                            updated_items.append(updated_item)
                            logger.info(
                                f"Successfully updated item and price history for CEX ID: {item.cex_id}"
                            )
                    except DatabaseError as e:
                        logger.exception(
                            f"Database error during price update for CEX ID {item.cex_id}: {e}"
                        )
                        continue
                    except Exception as e:
                        logger.exception(
                            f"Unexpected error during price update for CEX ID {item.cex_id}: {e}"
                        )
                        continue
            logger.info("Price updates completed successfully")
            return updated_items
        except Exception as e:
            logger.exception(
                "An unexpected error occurred for checking item prices: %s", e
            )
            return None

    def _validate_price_data(self, fetched_item_data):
        sell_price = fetched_item_data.sellPrice
        cash_price = fetched_item_data.cashPrice
        exchange_price = fetched_item_data.exchangePrice

        price_data_not_none = (
            sell_price is not None
            and cash_price is not None
            and exchange_price is not None
        )

        price_data_valid_range = (
            sell_price >= 0
            and cash_price >= 0
            and exchange_price >= 0
            and sell_price <= 3000
            and cash_price <= 3000
            and exchange_price <= 3000
        )

        return price_data_not_none and price_data_valid_range
