# Assigning items to users
# Deleted item/relationship
# Checking if a user owns an item
# Fetching all relationships

import logging
from django.db import IntegrityError, DatabaseError, transaction
from django.contrib.auth import get_user_model
from items.models.db_models import Item, UserItem

logger = logging.getLogger(__name__)


class UserItemService:
    def __init__(self):
        pass

    def user_owns_item(self, user, item) -> bool:
        # TODO: Validate inputs
        return UserItem.objects.filter(user=user, item=item).exists()

    def add_user_item(self, user, item):
        if self.user_owns_item(user, item):
            logger.info(f"User {user.username} already owns item {item.cex_id}")
            return None

        try:
            user_item = UserItem.objects.create(user=user, item=item)
            logger.info(
                f"User {user.username} added item {item.cex_id} to their collection."
            )
            return user_item
        except DatabaseError as e:
            logger.exception(f"Database error while adding user to item: {e}")
            return None
        except IntegrityError as e:
            logger.error(f"IntegrityError while adding user-item relation: {e}")
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred when adding user-item relation: {e}"
            )
            return None

    def delete_user_item(self, user, item):
        if not self.user_owns_item(user, item):
            logger.info(f"User {user.username} doesn't own item {item.cex_id}")
            return False

        try:
            with transaction.atomic():
                user_item = UserItem.objects.filter(user=user, item=item)
                deleted_count, _ = user_item.delete()

                if deleted_count == 1:
                    logger.info(
                        f"User {user.username} added item {item.cex_id} to their collection."
                    )
                    return True
                else:
                    raise Exception(
                        f"Failed to delete item with cex_id {item.cex_id}, tried to delete {deleted_count} items"
                    )
        except DatabaseError as e:
            logger.exception(f"Database error while deleting user from item: {e}")
            return False
        except IntegrityError as e:
            logger.error(f"IntegrityError while adding user-item relation: {e}")
            return False
        except Exception as e:
            logger.error(
                f"An unexpected error occurred when adding user-item relation: {e}"
            )
            return False

    def _validate_user_item_inputs(self, user, item) -> bool:
        User = get_user_model()

        if user is None or item is None:
            logger.error("Either user or item is None, cannot proceed.")
            return False

        if not isinstance(user, User):
            logger.error(f"Invalid item type. Expected '{User}', got {type(item)}")
            return False

        if not isinstance(item, Item):
            logger.error(f"Invalid item type. Expected 'Item', got {type(item)}")
            return False

        return True
