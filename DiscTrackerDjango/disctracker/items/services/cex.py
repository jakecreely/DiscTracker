import requests
from datetime import datetime

from ..models import Item, PriceHistory

def fetch_item(cex_id):
    try:
        search_url = f'https://wss2.cex.uk.webuy.io/v3/boxes/{cex_id}/detail'
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        return data['response']['data']
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error when fetching item by CEX ID: {e}")
        return None
    except requests.exceptions.JSONDecodeError as e:
        print(f"Failed to parse JSON response for CEX ID {cex_id}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for fetching item by CEX ID {cex_id}: {e}")
        return None

def check_price_updates():
    try: 
        items = Item.objects.all()

        for item in items:
            cex_id = item.cex_id
            # current_sell_price = item.sell_price
            current_exchange_price = item.exchange_price
            current_cash_price = item.cash_price

            response = requests.get(f'https://wss2.cex.uk.webuy.io/v3/boxes/{cex_id}/detail')
            response.raise_for_status()
            
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
        return "Price updates completed successfully."
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error when fetching item by CEX ID: {e}")
        return None
    except requests.exceptions.JSONDecodeError as e:
        print(f"Failed to parse JSON response for CEX ID {cex_id}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for checking item prices: {e}")
        return None