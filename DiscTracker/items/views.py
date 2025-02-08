from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.db import DatabaseError
from django.http import Http404
from django.core.paginator import Paginator
import logging

from items.models.db_models import Item, PriceHistory
from items.services import cex 
from items.forms import AddItemForm, UpdateItemPrices

logger = logging.getLogger(__name__)

def index(request):
    if request.method == "GET":
        try:          
            logger.info("Fetching all items for index view")  
            items_list = Item.objects.all()
            
            NUMBER_OF_ITEMS_PER_PAGE = 9
            paginator = Paginator(items_list, NUMBER_OF_ITEMS_PER_PAGE)

            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            
            context = {
                "items_list": page_obj.object_list,
                "page_obj": page_obj,
                "add_item_form": AddItemForm,
                "update_item_prices_form": UpdateItemPrices
            }
            
            return render(request, "items/index.html", context)
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)
            return render(request, "error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e: 
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "error.html", {"message": "An unexpected error occurred: " + str(e)})
    else:
        logger.warning("Invalid request method (%s) - GET required", request.method)
        return render(request, "error.html", {"message": "Invalid request method - GET required"})
        

def detail(request, item_id):
    if request.method == "GET":
        try:            
            logger.info("Fetching item %s for detail view", item_id)  
            item = get_object_or_404(Item, pk=item_id)
            price_history = item.price_history.all()
            return render(request, "items/detail.html", {"item": item, "price_history": price_history})
        except Http404 as e:
            logger.exception("Error fetching item by item_id %s: %s", item_id, e)
            return render(request, "error.html", {"message": "Error fetching item by item_id: " + str(e)})
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)
            return render(request, "error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "error.html", {"message": "An unexpected error occurred: " + str(e)})
    else:
        logger.warning("Invalid request method (%s) - GET required")
        return render(request, "error.html", {"message": "Invalid request method - GET required"})

def price_history(request):
    if request.method == "GET":
        try:            
            logger.info("Fetching price history for price_history view")  
            price_history = get_list_or_404(PriceHistory)
            return render(request, "items/price_history.html", {"item": price_history})
        except Http404 as e:
            logger.exception("Error fetching price history: %s", e)
            return render(request, "error.html", {"message": "Error fetching price history: " + str(e)})
        except DatabaseError as e:  
            logger.exception("Database error occured: %s", e)        
            return render(request, "error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "error.html", {"message": "An unexpected error occurred: " + str(e)})   
    else:
        logger.warning("Invalid request method (%s) - GET required")
        return render(request, "error.html", {"message": "Invalid request method - GET required"})
        
def add_item_from_cex(request):
    if request.method == "POST":
        logger.info("Retrieving cex_id from request")  
        cex_id = request.POST.get("cex_id")
        
        if not cex_id:
            logger.warning("cex_id does not exist")  
            return redirect("items:index")
        
        try:
            logger.info("Fetching item by cex_id %s", cex_id)  
            cex_data = cex.fetch_item(cex_id)

            if cex_data is None:
                logger.error("Fetched item with cex_id %s is empty", cex_id)  
                return render(request, "error.html", {"message": "Failed to fetch data from CEX"})

            logger.info("Creating or updating item in database")
            item = cex.create_or_update_item(cex_data)

            logger.info("Creating price history entry for item %s", cex_id)  
            price_history = cex.create_price_history_entry(item)
            
            logger.info("Redirecting to items index")  
            return redirect("items:index")
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)        
            return render(request, "error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e: 
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "error.html", {"message": "An unexpected error occurred: " + str(e)})
    else:
        logger.warning("Invalid request method (%s) - POST required")
        return render(request, "error.html", {"message": "Invalid request method - POST required"})
    
def update_item_prices(request):
    try:
        logger.info("Updating item prices")  
        cex.check_price_updates()
        logger.info("Redirecting to items index")  
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return render(request, "error.html", {"message": "An unexpected error occurred: " + str(e)})