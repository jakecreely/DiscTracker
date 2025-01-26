from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from datetime import datetime

from .models import Item, PriceHistory
from .services.cex import fetch_item

def index(request):
    items_list = Item.objects.all()
    context = {"items_list": items_list}
    return render(request, "discs/index.html", context)

def detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    return render(request, "discs/detail.html", {"item": item})

def price_history(request):
    price_history = get_list_or_404(PriceHistory)
    return render(request, "discs/price_history.html", {"item": price_history})

def add_item_from_cex(request):
    if request.method == "POST":
        cex_id = request.POST.get("cex_id")
        
        if not cex_id:
            return redirect("discs:index")
        
        try:
            cex_data = fetch_item(cex_id)
            
            if cex_data is None:
                return render(request, "error.html", {"message": "Failed to fetch data from CEX."})
                
            title = cex_data['boxDetails'][0]['boxName']
            cex_id = cex_data['boxDetails'][0]['boxId']
            sell_price = cex_data['boxDetails'][0]['sellPrice']
            exchange_price = cex_data['boxDetails'][0]['exchangePrice']
            cash_price = cex_data['boxDetails'][0]['cashPrice']

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
                item.title = title
                item.sell_price = sell_price
                item.exchange_price = exchange_price
                item.cash_price = cash_price
                item.last_checked = datetime.now()
                item.save()
                
            PriceHistory.objects.create(
                item=item,
                sell_price=sell_price,
                exchange_price=exchange_price,
                cash_price=cash_price,
                date_checked=datetime.now(),
            )
            
        except Exception as e:
            print(f"Error while adding item from CEX API: {e}")
            #return redirect("add-item")