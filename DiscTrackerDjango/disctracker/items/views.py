from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.db import DatabaseError
from django.http import Http404
from datetime import datetime

from .models import Item, PriceHistory
from .services.cex import fetch_item, check_price_updates

logger = logging.getLogger(__name__)

def index(request):
    if request.method == "GET":
        try:          
            logger.info("Fetching all items for index view")  
            items_list = Item.objects.all()
            context = {"items_list": items_list}
            return render(request, "items/index.html", context)
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)
            return render(request, "items/error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e: 
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "items/error.html", {"message": "An unexpected error occurred: " + str(e)})
    else:
        logger.warning("Invalid request method (%s) - GET required", request.method)
        return render(request, "items/error.html", {"message": "Invalid request method - GET required"})
        

def detail(request, item_id):
    if request.method == "GET":
        try:            
            logger.info("Fetching item %s for detail view", item_id)  
            item = get_object_or_404(Item, pk=item_id)
            price_history = item.price_history.all()
            return render(request, "items/detail.html", {"item": item, "price_history": price_history})
        except Http404 as e:
            logger.exception("Error fetching item by item_id %s: %s", item_id, e)
            return render(request, "items/error.html", {"message": "Error fetching item by item_id: " + str(e)})
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)
            return render(request, "items/error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "items/error.html", {"message": "An unexpected error occurred: " + str(e)})
    else:
        logger.warning("Invalid request method (%s) - GET required")
        return render(request, "items/error.html", {"message": "Invalid request method - GET required"})

def price_history(request):
    if request.method == "GET":
        try:            
            logger.info("Fetching price history for price_history view")  
            price_history = get_list_or_404(PriceHistory)
            return render(request, "items/price_history.html", {"item": price_history})
        except Http404 as e:
            logger.exception("Error fetching price history: %s", e)
            return render(request, "items/error.html", {"message": "Error fetching price history: " + str(e)})
        except DatabaseError as e:  
            logger.exception("Database error occured: %s", e)        
            return render(request, "items/error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e:
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "items/error.html", {"message": "An unexpected error occurred: " + str(e)})   
    else:
        logger.warning("Invalid request method (%s) - GET required")
        return render(request, "items/error.html", {"message": "Invalid request method - GET required"})
        
def add_item_from_cex(request):
    if request.method == "POST":
        logger.info("Retrieving cex_id from request")  
        cex_id = request.POST.get("cex_id")
        
        if not cex_id:
            logger.warning("cex_id does not exist")  
            return redirect("items:index")
        
        try:
            logger.info("Fetching item by cex_id %s", cex_id)  
            cex_data = fetch_item(cex_id)
            
            if cex_data is None:
                logger.error("Fetched item with cex_id %s is empty", cex_id)  
                return render(request, "error.html", {"message": "Failed to fetch data from CEX"})
                
            logger.info("Extracting data from cex_data")  
            title = cex_data['boxDetails'][0]['boxName']
            cex_id = cex_data['boxDetails'][0]['boxId']
            sell_price = cex_data['boxDetails'][0]['sellPrice']
            exchange_price = cex_data['boxDetails'][0]['exchangePrice']
            cash_price = cex_data['boxDetails'][0]['cashPrice']

            logger.info("Fetching or creating item in database")  
            item, created = Item.objects.get_or_create(
                cex_id=cex_id,
                defaults={
                    "title": title,
                    "sell_price": sell_price,
                    "exchange_price": exchange_price,
                    "cash_price": cash_price,
                    "last_checked": datetime.now(),
                }
            )
            
            if not created:
                logger.info("Updating item %s in database", cex_id)  
                item.title = title
                item.sell_price = sell_price
                item.exchange_price = exchange_price
                item.cash_price = cash_price
                item.last_checked = datetime.now()
                item.save()
                
            logger.info("Creating price history entry for item %s", cex_id)  
            PriceHistory.objects.create(
                item=item,
                sell_price=sell_price,
                exchange_price=exchange_price,
                cash_price=cash_price,
                date_checked=datetime.now(),
            )
            
            logger.info("Redirecting to items index")  
            return redirect("items:index")
        except DatabaseError as e:
            logger.exception("Database error occured: %s", e)        
            return render(request, "items/error.html", {"message": "Database error occurred: " + str(e)})
        except Exception as e: 
            logger.exception("An unexpected error occured: %s", e)
            return render(request, "items/error.html", {"message": "An unexpected error occurred: " + str(e)})
    else:
        logger.warning("Invalid request method (%s) - POST required")
        return render(request, "items/error.html", {"message": "Invalid request method - POST required"})
    
def update_item_prices(request):
    try:
        logger.info("Updating item prices")  
        check_price_updates()
        logger.info("Redirecting to items index")  
        return redirect("items:index")
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return render(request, "items/error.html", {"message": "An unexpected error occurred: " + str(e)})