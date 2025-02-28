import logging
from celery import shared_task
from items.services.cex import check_price_updates

logger = logging.getLogger(__name__)


@shared_task
def update_prices_task():
    logger.info("Starting Check Price Updates Task")
    check_price_updates()
    logger.info("Prices Updated")
