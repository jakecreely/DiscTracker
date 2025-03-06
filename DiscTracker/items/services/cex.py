import requests
import logging
from datetime import date
from pydantic import ValidationError
from django.db import DatabaseError

from items.models.db_models import Item, PriceHistory, UserItem
from items.models.pydantic_models import (
    CexItemApiResponseWrapper,
    CexIdValidator,
    CexApiItemDetail,
)

logger = logging.getLogger(__name__)

CEX_API_BASE_URL = "https://wss2.cex.uk.webuy.io/v3/boxes"


def fetch_item(cex_id):
    try:
        if not cex_id:
            logger.error("CEX ID not provided: %s", cex_id)
            return None

        validated_cex_id_input = CexIdValidator(cex_id=cex_id)
        cex_id = validated_cex_id_input.cex_id

        search_url = f"{CEX_API_BASE_URL}/{cex_id}/detail"
        response = requests.get(search_url)

        if response.status_code == 404:
            logger.warning("CEX with ID %s not found", cex_id)
            return None

        response.raise_for_status()

        response_json = response.json()

        validated_response = CexItemApiResponseWrapper.model_validate(response_json)

        box_details = validated_response.response.data.boxDetails

        if len(box_details) == 1:
            logger.info("Successfully fetched item with CEX ID %s", cex_id)
            return box_details[0]
        else:
            logger.error(
                "Box Detail contains more than one element (%s)", len(box_details)
            )
            return None

    except ValidationError as e:
        logger.exception("Error validating API response", e)
        return None
    except requests.exceptions.HTTPError as e:
        logger.exception("HTTP Error when fetching item by CEX ID %s: %s", cex_id, e)
        return None
    except requests.exceptions.JSONDecodeError as e:
        logger.exception("Failed to parse JSON response for CEX ID %s: %s", cex_id, e)
        return None
    except Exception as e:
        logger.exception(
            "An unexpected error occurred for fetching item by CEX ID %s: %s", cex_id, e
        )
        return None


def fetch_user_items(user):
    items_list = Item.objects.filter(useritem__user=user).order_by("title")

    return items_list


# Only accepts CEX API Item Response
def create_or_update_item(item_data, user):
    if item_data is None:
        logger.error("Cex data is None, cannot create item")
        return None

    try:
        validated_item_data = CexApiItemDetail.model_validate(
            item_data
        )  # Check if json then call model_validate_json

        cex_id = validated_item_data.boxId  # TODO: Validate box_id using regex before

        logger.info("Creating item in database")
        item, item_created = Item.objects.get_or_create(
            cex_id=cex_id,
            defaults={
                "title": validated_item_data.boxName,
                "sell_price": validated_item_data.sellPrice,
                "exchange_price": validated_item_data.exchangePrice,
                "cash_price": validated_item_data.cashPrice,
                "last_checked": date.today(),
            },
        )

        UserItem.objects.get_or_create(user=user, item=item)

        if item_created:
            logger.info("Created item %s in database", cex_id)
            return item
        else:
            logger.info("Updating item %s in database", cex_id)
            item.title = validated_item_data.boxName
            item.sell_price = validated_item_data.sellPrice
            item.exchange_price = validated_item_data.exchangePrice
            item.cash_price = validated_item_data.cashPrice
            item.last_checked = date.today()
            item.save()
            logger.info("Updated item %s in database", cex_id)
            return item
    except ValidationError as e:
        logger.exception("Error validating item data", e)
        return None
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return None
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return None


def create_or_update_item_and_price_history(item_data, user):
    if item_data is None:
        logger.error("Item data is None, cannot create item")
        return None, None

    try:
        item = create_or_update_item(item_data, user)

        if item is None:
            logger.error("Failed to create or update item with data: %s", item_data)
            return None, None

        latest_price_history = (
            PriceHistory.objects.filter(item=item).order_by("-date_checked").first()
        )

        should_create_price_history = False

        if latest_price_history:
            if (
                latest_price_history.sell_price != item.sell_price
                or latest_price_history.exchange_price != item.exchange_price
                or latest_price_history.cash_price != item.cash_price
            ):
                should_create_price_history = True
            else:
                should_create_price_history = False  # No change, just easier to read
        else:
            should_create_price_history = True

        if should_create_price_history:
            price_history_entry = create_price_history_entry(item)

            if price_history_entry is None:
                logger.error(
                    "Failed to create price history entry for item with CEX ID: %s",
                    item.cex_id,
                )
                return item, None

            return item, price_history_entry
        else:
            return item, None
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return None, None
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return None, None


def delete_item(item_cex_id, user):
    if not item_cex_id:
        logger.error("Item CEX ID not provided: %s", item_cex_id)
        return False

    try:
        item = Item.objects.get(cex_id=item_cex_id)

        if not item:
            logger.error("Item with cex_id %s not found", item_cex_id)
            return False

        user_item_deleted_count, _ = UserItem.objects.get(user=user, item=item).delete()

        if user_item_deleted_count == 1:
            logger.info("Removed item %s from user %s", item_cex_id, user.username)
            return True
        elif user_item_deleted_count > 1:
            logger.error(
                "Deleted more than one UserItem entry for user %s and item %s",
                user.username,
                item_cex_id,
            )
            return False
        else:
            logger.warning(
                "No UserItem found for user %s and item %s", user.username, item_cex_id
            )
            return False
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return False
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return False


def create_price_history_entry(item):
    if not item:
        logger.error("Item is None, cannot create price history entry")
        return None

    if not isinstance(item, Item):
        logger.error("Invalid item type, expected Item model instead of %s", type(item))
        return None

    try:
        item.full_clean()
    except ValidationError as e:
        logger.error("Item failed validation: %s", e)
        return None

    try:
        price_entry = PriceHistory.objects.create(
            item=item,
            sell_price=item.sell_price,
            exchange_price=item.exchange_price,
            cash_price=item.cash_price,
            date_checked=date.today(),
        )
        logger.info("Created price history entry for item %s", item.cex_id)
        return price_entry
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return None
    except AttributeError as e:
        logger.exception("Missing attributes: %s", e)
        return None
    except Exception as e:
        logger.exception(
            "Failed to create price history entry for item %s: %s", item.cex_id, e
        )
        return None


def check_price_updates():
    updated_items = []

    try:
        logger.info("Starting price update check.")
        items = Item.objects.all()

        for item in items:
            if not item.cex_id:
                logger.warning("Item has no cex_id so skipping")
                continue

            logger.info("Fetching data for CEX ID: %s", item.cex_id)

            fetched_item_data = fetch_item(item.cex_id)

            if not fetched_item_data:
                logger.warning("No fetched data for CEX ID %s so skipping", item.cex_id)
                continue

            new_sell_price = fetched_item_data.sellPrice
            new_cash_price = fetched_item_data.cashPrice
            new_exchange_price = fetched_item_data.exchangePrice

            price_data_not_none = (
                new_sell_price is not None
                and new_cash_price is not None
                and new_exchange_price is not None
            )

            price_data_valid_range = (
                new_sell_price >= 0
                and new_cash_price >= 0
                and new_exchange_price >= 0
                and new_sell_price <= 3000
                and new_cash_price <= 3000
                and new_exchange_price <= 3000
            )

            price_data_valid = price_data_not_none and price_data_valid_range

            price_changed = (
                item.sell_price != new_sell_price
                or item.exchange_price != new_exchange_price
                or item.cash_price != new_cash_price
            )

            if price_data_valid:
                if price_changed:
                    logger.info("Updating prices for CEX ID: %s", item.cex_id)
                    item.sell_price = new_sell_price
                    item.cash_price = new_cash_price
                    item.exchange_price = new_exchange_price
                    item.last_checked = date.today()
                    item.save()
                    logger.info("Updated prices for CEX ID: %s", item.cex_id)

                    PriceHistory.objects.create(
                        item=item,
                        sell_price=new_sell_price,
                        exchange_price=new_exchange_price,
                        cash_price=new_cash_price,
                        date_checked=date.today(),
                    )
                    logger.info("Price history recorded for CEX ID: %s", item.cex_id)

                    updated_items.append(item)
                else:
                    logger.info(
                        "No price changes for CEX ID: %s, skipping save", item.cex_id
                    )
            else:
                logger.warning(
                    "New cash or exchange price is None for CEX ID: %s", item.cex_id
                )

        logger.info("Price updates completed successfully")
        return updated_items
    except requests.exceptions.HTTPError as e:
        logger.exception(
            "HTTP Error when fetching item by CEX ID %s: %s", item.cex_id, e
        )
        return None
    except requests.exceptions.JSONDecodeError as e:
        logger.exception(
            "Failed to parse JSON response for CEX ID %s: %s", item.cex_id, e
        )
        return None
    except Exception as e:
        logger.exception("An unexpected error occurred for checking item prices: %s", e)
        return None
