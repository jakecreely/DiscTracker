import logging
from celery import shared_task

from items.services.cex_service import CexService
from items.services.item_service import ItemService
from items.services.price_history_service import PriceHistoryService
from items.services.price_update_service import PriceUpdateService
from items.services.user_item_service import UserItemService
from items.validators.item_validator import ItemDataValidator

logger = logging.getLogger(__name__)


@shared_task
def update_prices_task():
    validator = ItemDataValidator()
    api_service = CexService()
    price_history_service = PriceHistoryService()
    user_item_service = UserItemService()
    item_service = ItemService(
        validator=validator,
        user_item_service=user_item_service,
        price_history_service=price_history_service,
    )
    price_update_service = PriceUpdateService(
        item_service=item_service,
        api_service=api_service,
        price_history_service=price_history_service,
    )

    logger.info("Starting Check Price Updates Task")
    price_update_service.check_price_updates()
    logger.info("Prices Updated")
