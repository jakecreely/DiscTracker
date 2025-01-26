import requests
from datetime import datetime

from ..models import Item, PriceHistory

def fetch_item(cex_id):
    search_url = f'https://wss2.cex.uk.webuy.io/v3/boxes/{cex_id}/detail'
    response = requests.get(search_url)
    if response.status_code == 200:
        try:
            data = response.json()
            return data['response']['data']
        except:
            print('Failed to parse JSON response')
            return None
    else:
        print('Failed To Fetch Item')
        return None

def check_price_updates():
    items = Item.objects.all()

    for item in items:
        cex_id = item.cex_id
        current_sell_price = item.sell_price
        current_exchange_price = item.exchange_price
        current_cash_price = item.cash_price

        response = requests.get(f'https://wss2.cex.uk.webuy.io/v3/boxes/{cex_id}/detail')
        
        if response.status_code == 200:
            data = response.json()['response']['data']
            new_sell_price = data['boxDetails'][0]['sellPrice']
            new_cash_price = data['boxDetails'][0]['cashPrice']
            new_exchange_price = data['boxDetails'][0]['exchangePrice']
            
            if new_cash_price and new_exchange_price is not None:
                if new_cash_price > current_cash_price and new_exchange_price > current_exchange_price:
                    item.sell_price = new_sell_price
                    item.cash_price = new_cash_price
                    item.exchange_price = new_exchange_price
                    item.save()
                elif new_cash_price > current_cash_price and new_exchange_price <= current_exchange_price:
                    item.sell_price = new_sell_price
                    item.cash_price = new_cash_price
                    item.save()
                elif new_cash_price <= current_cash_price and new_exchange_price > current_exchange_price:
                    item.sell_price = new_sell_price
                    item.exchange_price = new_exchange_price
                    item.save()
                
                PriceHistory.objects.create(
                    item=item,
                    sell_price=new_sell_price,
                    exchange_price=new_exchange_price,
                    cash_price=new_cash_price,
                    date_checked=datetime.now(),
                )                
            else:
                print(f"Price not found for ID {cex_id}")
        else:
            print(f"Failed to fetch data for ID {cex_id}")