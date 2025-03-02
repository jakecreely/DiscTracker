from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
import logging

from items.models.db_models import Item, PriceHistory
from items.services import cex
from items.forms import AddItemForm, UpdateItemPrices
from items.tasks import update_prices_task

logger = logging.getLogger(__name__)


def index(request):
    if request.method != "GET":
        logger.warning("Invalid request method (%s) - GET required", request.method)
        messages.warning(request, "Invalid request method - only GET is allowed.")
        return redirect("items:index")

    try:
        logger.info("Fetching all items for index view")
        items_list = Item.objects.all().order_by("title")

        NUMBER_OF_ITEMS_PER_PAGE = 9
        paginator = Paginator(items_list, NUMBER_OF_ITEMS_PER_PAGE)

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "items_list": page_obj.object_list,
            "page_obj": page_obj,
            "add_item_form": AddItemForm,
            "update_item_prices_form": UpdateItemPrices,
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


def detail(request, item_id):
    if request.method != "GET":
        logger.warning("Invalid request method (%s) - GET required", request.method)
        messages.warning(request, "Invalid request method - only GET is allowed.")
        return redirect("items:index")

    try:
        logger.info("Fetching item %s for detail view", item_id)
        item = get_object_or_404(Item, pk=item_id)
        return render(request, "items/detail.html", {"item": item})
    except Http404 as e:
        logger.exception("Error fetching item by item_id %s: %s", item_id, e)
        messages.error(request, f"Item with ID '{item_id}' not found.")
        return redirect("items:index")
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        messages.error(request, "Database error occurred. Please try again later.")
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("items:index")


def price_history(request):
    if request.method != "GET":
        logger.warning("Invalid request method (%s) - GET required", request.method)
        messages.warning(request, "Invalid request method - only GET is allowed.")
        return redirect("items:index")

    try:
        logger.info("Fetching price history for price_history view")
        price_history = get_list_or_404(PriceHistory)
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
        cex_data = cex.fetch_item(cex_id)

        if cex_data is None:
            logger.error("Fetched item with cex_id %s is empty", cex_id)
            messages.warning(request, f"Item with ID '{cex_id}' does not exist.")
            return redirect("items:index")

        logger.info("Creating or updating item in database")
        item = cex.create_or_update_item(cex_data)

        if not item:
            logger.info("Could not create item with ID %s", cex_id)
            messages.error(request, f"Could not add Item with ID '{cex_id}'.")
            return redirect("items:index")

        logger.info("Creating price history entry for item %s", cex_id)
        price_history = cex.create_price_history_entry(item)

        if not price_history:
            logger.info("Could not create price history entry for item %s", cex_id)
            messages.error(
                request, f"Could not create price history for item with ID '{cex_id}'."
            )
            return redirect("items:index")

        messages.info(request, f"Added/updated {item.title}!")
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


def item_price_chart(request, item_id):
    try:
        item = get_object_or_404(Item, pk=item_id)
        price_history = item.price_history.all().order_by("date_checked")

        if not price_history.exists():
            logger.warning(f"No price history found for item {item_id}")
            return JsonResponse(
                {"error": f"No price history available for item {item_id}"}, status=404
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
        logger.exception(f"Item with ID {item_id} not found")
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
