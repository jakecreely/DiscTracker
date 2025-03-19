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
from items.models.db_models import Item, PriceHistory, UserItem
from items.forms import AddItemForm, UpdateItemPrices, DeleteItemForm
from items.tasks import update_prices_task
from items.permissions import is_admin
from items.filters import ItemFilter

from django.utils.dateparse import parse_date
from datetime import timedelta
from django.utils import timezone

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

            messages.info(request, f"Added {item_data.title}.")
            logger.info("Redirecting to items index")
            return redirect("items:index")
        else:
            logger.info(f"Item {existing_item.title} exists")
            user_owns_item = user_item_service.user_owns_item(
                request.user, existing_item
            )
            if user_owns_item:
                logger.info(
                    f"User {request.user.username} already owns {existing_item.title}"
                )
                messages.info(request, f"You already own '{item_data.title}'.")
                return redirect("items:index")
            else:
                logger.info(
                    f"Assigning {existing_item.title} to user {request.user.username}"
                )
                user_existing_item = user_item_service.add_user_item(
                    request.user, item=existing_item
                )

                if not user_existing_item:
                    raise Exception(
                        f"Couldn't create user item relationship between {request.user.username} and {existing_item.title}"
                    )

                messages.info(request, f"Added {item_data.title}.")
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


def get_price_change_for_user(user, start_date, end_date):
    # Create an empty list to store price changes for each item
    price_changes = []

    # Iterate over all items the user has defined (through UserItem or similar model)
    for (
        user_item
    ) in user.useritem_set.all():  # Assuming useritem_set relates to UserItem model
        item = user_item.item  # Assuming `item` is a foreign key in the UserItem model

        # Get the price record closest to the start date
        start_record = (
            item.price_history.filter(date_checked__gte=start_date)
            .order_by("date_checked")
            .first()
        )

        # Get the price record closest to the end date
        end_record = (
            item.price_history.filter(date_checked__lte=end_date)
            .order_by("-date_checked")
            .first()
        )

        if start_record and end_record:
            sell_price_change = (
                100
                * (end_record.sell_price - start_record.sell_price)
                / start_record.sell_price
            )
            exchange_price_change = (
                100
                * (end_record.exchange_price - start_record.exchange_price)
                / start_record.exchange_price
            )
            cash_price_change = (
                100
                * (end_record.cash_price - start_record.cash_price)
                / start_record.cash_price
            )

            price_changed = (
                sell_price_change != 0
                or exchange_price_change != 0
                or cash_price_change != 0
            )

            if price_changed:
                # Append the price changes for this item to the list
                price_changes.append(
                    {
                        "item": item,
                        "start_date": start_record.date_checked,
                        "end_date": end_record.date_checked,
                        "sell_price_change": sell_price_change,
                        "exchange_price_change": exchange_price_change,
                        "cash_price_change": cash_price_change,
                    }
                )

    return price_changes


def get_price_trends_for_user(user, start_date, end_date):
    # Fetch all items associated with the user
    user_items = UserItem.objects.filter(user=user)

    # Create a list to store trends for all the user's items
    all_trends = []

    for user_item in user_items:
        # Fetch the price history for each item within the date range
        price_history = PriceHistory.objects.filter(
            item_id=user_item.item_id,
            date_checked__gte=start_date,
            date_checked__lte=end_date,
        ).order_by("date_checked")

        trends = []
        previous_sell_price = None
        previous_exchange_price = None
        previous_cash_price = None

        # Calculate price trends for each item
        for record in price_history:
            # Initialize percentage changes
            sell_price_percentage_change = None
            exchange_price_percentage_change = None
            cash_price_percentage_change = None

            # Calculate percentage changes
            if previous_sell_price is not None:
                sell_price_percentage_change = (
                    100
                    * (record.sell_price - previous_sell_price)
                    / previous_sell_price
                )
            if previous_exchange_price is not None:
                exchange_price_percentage_change = (
                    100
                    * (record.exchange_price - previous_exchange_price)
                    / previous_exchange_price
                )
            if previous_cash_price is not None:
                cash_price_percentage_change = (
                    100
                    * (record.cash_price - previous_cash_price)
                    / previous_cash_price
                )

            # Append the record and the calculated trends to the list
            trends.append(
                {
                    "item_id": record.item_id,
                    "date_checked": record.date_checked,
                    "sell_price": record.sell_price,
                    "exchange_price": record.exchange_price,
                    "cash_price": record.cash_price,
                    "sell_price_percentage_change": sell_price_percentage_change,
                    "exchange_price_percentage_change": exchange_price_percentage_change,
                    "cash_price_percentage_change": cash_price_percentage_change,
                }
            )

            logger.info(f"Sell Price Percentage Change: {sell_price_percentage_change}")
            logger.info(
                f"Exchange Price Percentage Change: {exchange_price_percentage_change}"
            )
            logger.info(f"Cash Price Percentage Change: {cash_price_percentage_change}")

            # Update previous prices for the next iteration
            previous_sell_price = record.sell_price
            previous_exchange_price = record.exchange_price
            previous_cash_price = record.cash_price

        # Add trends for this particular item to the all_trends list
        all_trends.append(
            {
                "user_item": user_item,  # Store the user_item object to display its details later
                "trends": trends,
            }
        )

    return all_trends


@login_required
def price_trends_view(request):
    # Get the current user
    user = request.user

    # Get the 'start_date' and 'end_date' from the query string, and parse them into datetime.date objects
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    # If no dates are provided, default to a period of 1 week ago to today
    if not start_date_str or not end_date_str:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=1)  # Default to 1 week range
    else:
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)

    # Get the price trends for all the user's items within the specified date range
    price_changes = get_price_change_for_user(user, start_date, end_date)

    # Render the template with the trends and the selected date range
    return render(
        request,
        "items/price_trends.html",
        {
            "price_changes": price_changes,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


# @login_required
# def price_trends_view(request):
#     # Get the current user
#     user = request.user

#     # Get the 'start_date' and 'end_date' from the query string, and parse them into datetime.date objects
#     start_date_str = request.GET.get('start_date')
#     end_date_str = request.GET.get('end_date')

#     # If no dates are provided, default to a period of 1 week ago to today
#     if not start_date_str or not end_date_str:
#         end_date = timezone.now().date()
#         start_date = end_date - timedelta(weeks=1)  # Default to 1 week range
#     else:
#         start_date = parse_date(start_date_str)
#         end_date = parse_date(end_date_str)

#     # Get the price trends for all the user's items within the specified date range
#     all_trends = get_price_trends_for_user(user, start_date, end_date)

#     # Render the template with the trends and the selected date range
#     return render(request, 'items/price_trends.html', {'all_trends': all_trends, 'start_date': start_date, 'end_date': end_date})
