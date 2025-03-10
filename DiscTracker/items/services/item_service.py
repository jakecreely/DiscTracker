import logging
from datetime import date
from typing import Optional, Tuple
from django.db import DatabaseError, transaction
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from items.services.price_history_service import PriceHistoryService
from items.services.user_item_service import UserItemService
from items.validators.item_validator import ItemDataValidator
from items.models.db_models import Item

logger = logging.getLogger(__name__)


class ItemService:
    def __init__(
        self,
        validator: ItemDataValidator,
        user_item_service: UserItemService,
        price_history_service: PriceHistoryService,
    ):
        self.validator = validator
        self.user_item_service = user_item_service
        self.price_history_service = price_history_service

    def get_item_by_cex_id(self, cex_id) -> Optional[Item]:
        try:
            logger.info(f"Fetching item by cex_id {cex_id}")
            item = Item.objects.get(cex_id=cex_id)
            return item
        except Item.DoesNotExist:
            print(f"No item found with cex_id: {cex_id}")
            return None
        except Item.MultipleObjectsReturned:
            print(f"Multiple items found with cex_id: {cex_id}")
            return None

    def get_all_items(self) -> QuerySet[Item]:
        return Item.objects.all()

    def get_user_items(self, user) -> QuerySet[Item]:
        if not isinstance(user, get_user_model()):
            raise ValueError("Invalid user type")

        return Item.objects.filter(useritem__user=user).order_by("title")

    def create_item(self, item_data) -> Tuple[Optional[Item], bool]:
        validated_item_data = self.validator.validate_item_data(item_data)
        if not validated_item_data:
            logger.error("Item data validation failed")
            return None, False

        try:
            cex_id = validated_item_data.cex_id

            logger.info(f"Fetching or creating item {cex_id}")
            item, item_created = Item.objects.get_or_create(
                cex_id=cex_id,
                defaults={
                    "title": validated_item_data.title,
                    "sell_price": validated_item_data.sell_price,
                    "exchange_price": validated_item_data.exchange_price,
                    "cash_price": validated_item_data.cash_price,
                    "last_checked": date.today(),
                },
            )

            if item_created:
                logger.info(f"Created item {cex_id}")
            else:
                logger.info(f"Item {cex_id} already exists")

            return item, item_created
        except DatabaseError as e:
            logger.exception(f"Database error occured: {e}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occured: {e}")
            return None

    def update_item(self, item_data) -> Optional[Item]:
        validated_item_data = self.validator.validate_item_data(item_data)
        if not validated_item_data:
            logger.error("Item data validation failed")
            return None

        try:
            cex_id = validated_item_data.cex_id

            logger.info(f"Updating item {cex_id}")
            item = Item.objects.get(cex_id=cex_id)

            item.title = validated_item_data.title
            item.sell_price = validated_item_data.sell_price
            item.exchange_price = validated_item_data.exchange_price
            item.cash_price = validated_item_data.cash_price
            item.last_checked = date.today()
            item.save()

            logger.info(f"Item {cex_id} updated successfully")
            return item
        except DatabaseError as e:
            logger.exception(f"Database error occured: {e}")
            return None
        except Item.DoesNotExist as e:
            logger.exception(f"Database error occured: {e}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occured: {e}")
            return None

    def delete_item(self, cex_id) -> bool:
        if not cex_id:
            logger.error("Item CEX ID not provided")
            return False

        try:
            with transaction.atomic():
                item_deleted_count, _ = Item.objects.get(cex_id=cex_id).delete()

                if item_deleted_count == 1:
                    logger.info(f"Removed item {cex_id}")
                    return True
                else:
                    raise Exception(
                        f"Failed to delete item with cex_id {cex_id}, tried to delete {item_deleted_count} items"
                    )
        except Item.DoesNotExist:
            logger.error(f"Item with cex_id %s not found {cex_id}")
            return False
        except Exception as e:
            logger.error(
                f"An unexpected error occured while deleting item {cex_id}: {e}"
            )
            return False

    def create_item_and_price_history(self, item_data, user):
        if item_data is None:
            logger.error("Item data is None, cannot create item")
            return None, None

        try:
            with transaction.atomic():
                item, item_created = self.create_item(item_data)

                if item is None:
                    logger.error(
                        "Failed to create or update item with data: %s", item_data
                    )
                    raise DatabaseError("Item Failed To Be Created")

                user_item = self.user_item_service.add_user_item(user, item)

                if not user_item:
                    logger.error("User already owns item with ID %s", item.cex_id)
                    raise DatabaseError("User Already Owns Item")

                if item_created:
                    price_history_entry = (
                        self.price_history_service.create_price_history_entry(item)
                    )
                    if price_history_entry is None:
                        logger.error(
                            "Failed to create price history entry for item with CEX ID: %s",
                            item.cex_id,
                        )
                        raise DatabaseError("Price History Failed To Be Created")
                    return item, price_history_entry
                else:
                    price_history_entry = self.price_history_service.create_price_history_if_price_changed(
                        item
                    )
                    if price_history_entry is None:
                        return item, None
                    return item, price_history_entry
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)
            return None, None
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return None, None
