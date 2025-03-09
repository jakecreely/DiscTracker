from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
import logging

from items.services.cex_service import CexService
from items.services.price_history_service import PriceHistoryService
from items.services.user_item_service import UserItemService
from items.validators.item_validator import ItemDataValidator
from items.services.item_service import ItemService
from items.models.db_models import Item, PriceHistory
from items.forms import AddItemForm, UpdateItemPrices, DeleteItemForm
from items.tasks import update_prices_task
from items.permissions import is_admin
from items.filters import ItemFilter

logger = logging.getLogger(__name__)


@login_required
def index(request):
    if request.method != "GET":
        logger.warning("Invalid request method (%s) - GET required", request.method)
        messages.warning(request, "Invalid request method - only GET is allowed.")
        return redirect("items:index")

    try:
        validator = ItemDataValidator()
        user_item_service = UserItemService()
        price_history_service = PriceHistoryService()

        item_service = ItemService(
            validator=validator,
            user_item_service=user_item_service,
            price_history_service=price_history_service,
        )

        logger.info("Fetching all items for index view")
        item_list = item_service.get_user_items(request.user)

        NUMBER_OF_ITEMS_PER_PAGE = 9
        item_filter = ItemFilter(request.GET, queryset=item_list)

        paginator = Paginator(item_filter.qs, NUMBER_OF_ITEMS_PER_PAGE)

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "items_list": page_obj.object_list,
            "page_obj": page_obj,
            "add_item_form": AddItemForm,
            "update_item_prices_form": UpdateItemPrices,
            "filter": item_filter,
        }

        return render(request, "items/index.html", context)
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        messages.error(request, "Database error occurred. Please try again later.")
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("items:index")


@login_required
def detail(request, cex_id):
    if request.method != "GET":
        logger.warning("Invalid request method (%s) - GET required", request.method)
        messages.warning(request, "Invalid request method - only GET is allowed.")
        return redirect("items:index")

    try:
        validator = ItemDataValidator()
        user_item_service = UserItemService()
        price_history_service = PriceHistoryService()

        item_service = ItemService(
            validator=validator,
            user_item_service=user_item_service,
            price_history_service=price_history_service,
        )

        logger.info("Fetching item %s for detail view", cex_id)
        item = item_service.get_item_by_cex_id(cex_id=cex_id)

        if not item:
            logger.exception(f"Error fetching item by cex_id {cex_id}")
            messages.error(request, f"Item with ID '{cex_id}' not found.")
            return redirect("items:index")

        context = {
            "item": item,
            "delete_item_form": DeleteItemForm,
        }

        return render(request, "items/detail.html", context)
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        messages.error(request, "Database error occurred. Please try again later.")
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("items:index")


@login_required
def price_history(request):
    if request.method != "GET":
        logger.warning("Invalid request method (%s) - GET required", request.method)
        messages.warning(request, "Invalid request method - only GET is allowed.")
        return redirect("items:index")

    try:
        logger.info("Fetching price history for price_history view")
        # TODO: Change to use item not user
        price_history = get_list_or_404(PriceHistory, item__user=request.user)
        return render(request, "items/price_history.html", {"item": price_history})
    except Http404 as e:
        logger.exception("Error fetching price history: %s", e)
        messages.warning(request, "No price history available.")
        return render(
            request,
            "error.html",
            {"message": "Error fetching price history: " + str(e)},
        )
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        messages.error(request, "Database error occurred. Please try again later.")
        return render(
            request, "error.html", {"message": "Database error occurred: " + str(e)}
        )
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(
            request,
            "error.html",
            {"message": "An unexpected error occurred: " + str(e)},
        )


@login_required
def add_item_from_cex(request):
    if request.method != "POST":
        logger.warning("Invalid request method (%s) - POST required", request.method)
        messages.warning(request, "Invalid request method - only POST is allowed.")
        return redirect("items:index")

    logger.info("Retrieving cex_id from request")
    cex_id = request.POST.get("cex_id")

    if not cex_id:
        logger.warning("cex_id does not exist")
        messages.warning(request, "CEX ID is missing so cannot add item.")
        return redirect("items:index")

    try:
        logger.info("Fetching item by cex_id %s", cex_id)

        validator = ItemDataValidator()
        user_item_service = UserItemService()
        price_history_service = PriceHistoryService()

        item_service = ItemService(
            validator=validator,
            user_item_service=user_item_service,
            price_history_service=price_history_service,
        )
        cex_service = CexService()

        item_data = cex_service.fetch_item(cex_id)

        if item_data is None:
            logger.error("Fetched item with cex_id %s is empty", cex_id)
            messages.warning(request, f"Item with ID '{cex_id}' does not exist.")
            return redirect("items:index")

        existing_item = item_service.get_item_by_cex_id(item_data.cex_id)

        if not existing_item:
            logger.info(f"Creating item {item_data.cex_id} in database")
            item, _ = item_service.create_item_and_price_history(
                item_data=item_data, user=request.user
            )

            if not item:
                logger.info("Could not create item with ID %s", cex_id)
                messages.error(request, f"Could not add Item with ID '{cex_id}'.")
                return redirect("items:index")

        user_owns_item = user_item_service.user_owns_item(request.user, existing_item)

        if user_owns_item:
            messages.info(request, f"You already own '{item_data.title}'.")
            return redirect("items:index")
        messages.info(request, f"Added {item.title}.")
        logger.info("Redirecting to items index")
        return redirect("items:index")
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        messages.error(request, "Database error occurred. Please try again later.")
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("items:index")


@login_required
def delete_item(request, cex_id):
    if request.method != "POST":
        logger.warning("Invalid request method (%s) - POST required", request.method)
        messages.warning(request, "Invalid request method - only POST is allowed.")
        return redirect("items:index")

    logger.info("Retrieving cex_id from request")

    if not cex_id:
        logger.warning("cex_id does not exist")
        messages.warning(request, "Item CEX ID is missing so cannot delete item.")
        return redirect("items:index")

    try:
        validator = ItemDataValidator()
        user_item_service = UserItemService()
        price_history_service = PriceHistoryService()

        item_service = ItemService(
            validator=validator,
            user_item_service=user_item_service,
            price_history_service=price_history_service,
        )

        item = item_service.get_item_by_cex_id(cex_id=cex_id)

        item_deleted = user_item_service.delete_user_item(item=item, user=request.user)

        if item_deleted:
            messages.success(request, "Deleted item successfully!")
            logger.info("Deleted item with CEX ID %s", cex_id)
            return redirect("items:index")
        else:
            messages.error(request, "Failed to delete item!")
            logger.error("Failed to delete item with CEX ID %s", cex_id)
            return redirect("items:index")
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        messages.error(request, "Database error occurred. Please try again later.")
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("items:index")


@user_passes_test(is_admin, login_url="/accounts/login/")
def update_item_prices(request):
    try:
        messages.info(request, "Price update is in progress. Check back soon!")
        update_prices_task.delay()
        logger.info("Redirecting to items index")
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("items:index")


@login_required
def item_price_chart(request, cex_id):
    try:
        item = get_object_or_404(Item, cex_id=cex_id)
        price_history = item.price_history.all().order_by("date_checked")

        if not price_history.exists():
            logger.warning(f"No price history found for item {cex_id}")
            return JsonResponse(
                {"error": f"No price history available for item {cex_id}"}, status=404
            )

        labels = []
        sell_prices = []
        exchange_prices = []
        cash_prices = []

        for entry in price_history:
            labels.append(
                entry.date_checked.strftime("%Y-%m-%d")
            )  # Has to be string for json
            sell_prices.append(
                float(entry.sell_price)
            )  # Has to change from Decimal to float to json serialise
            exchange_prices.append(
                float(entry.exchange_price)
            )  # Has to change from Decimal to float to json serialise
            cash_prices.append(
                float(entry.cash_price)
            )  # Has to change from Decimal to float to json serialise

        data = {
            "labels": labels,
            "datasets": [
                {
                    "label": "Sell Price",
                    "data": sell_prices,
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "fill": False,
                },
                {
                    "label": "Exchange Price",
                    "data": exchange_prices,
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "fill": False,
                },
                {
                    "label": "Cash Price",
                    "data": cash_prices,
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "fill": False,
                },
            ],
        }

        return JsonResponse(data)

    except Http404:
        logger.exception(f"Item with ID {cex_id} not found")
        return JsonResponse({"error": "Item not found."}, status=404)
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return JsonResponse(
            {"error": "Database error. Please try again later."}, status=500
        )
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again later."},
            status=500,
        )
