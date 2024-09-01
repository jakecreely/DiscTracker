import requests
from DiscTracker.database import get_all_items, update_price_in_database, add_item_to_price_history

def check_price_updates():
    # Fetch items - id and current price (cash and exchange)
    items = get_all_items()
    
    for item in items:
        print(item)
        # (1, 'Blu-ray', 12345, 10.00, 5.00, '2024-09-01')
        item_id = item[2]
        current_cash_price = item[4]
        current_exchange_price = item[3]
        
        response = requests.get(f'https://wss2.cex.uk.webuy.io/v3/boxes/{item_id}/detail')
        if response.status_code == 200:
            data = response.json()['response']['data']
            new_cash_price = data['boxDetails'][0]['cashPrice']
            new_exchange_price = data['boxDetails'][0]['exchangePrice']
            
            if new_cash_price and new_exchange_price is not None:
                # If cash and exchange is both greater than current prices then update both
                if new_cash_price > current_cash_price and new_exchange_price > current_exchange_price:
                    update_price_in_database(item_id, new_cash_price, new_exchange_price)
                # If only cash is greater than current price then update item with new cash
                elif new_cash_price > current_cash_price and new_exchange_price <= current_exchange_price:
                    update_price_in_database(item_id, new_cash_price, current_exchange_price)
                # If only exchange is greater than current price then update item with new exchange
                elif new_cash_price <= current_cash_price and new_exchange_price > current_exchange_price:
                    update_price_in_database(item_id, current_cash_price, new_exchange_price)
                # Record the new price history
                add_item_to_price_history(item_id, new_exchange_price, new_cash_price)
            else:
                print(f"Price not found for ID {item_id}")
        else:
            print(f"Failed to fetch data for ID {item_id}")
