import requests
import pandas as pd
from DiscTracker.database import get_all_items, update_price_in_database, add_item_to_price_history, fetch_price_changes

def check_price_updates():
    # Fetch items - id and current price (cash and exchange)
    items = get_all_items()
    
    for item in items:
        # (1, 'Blu-ray', 12345, SELL_PRICE, 10.00, 5.00, '2024-09-01')
        item_id = item.cex_id
        current_sell_price = item.sell_price
        current_exchange_price = item.exchange_price
        current_cash_price = item.cash_price
        
        response = requests.get(f'https://wss2.cex.uk.webuy.io/v3/boxes/{item_id}/detail')
        if response.status_code == 200:
            data = response.json()['response']['data']
            new_sell_price = data['boxDetails'][0]['sellPrice']
            new_cash_price = data['boxDetails'][0]['cashPrice']
            new_exchange_price = data['boxDetails'][0]['exchangePrice']
                        
            if new_cash_price and new_exchange_price is not None:
                # If cash and exchange is both greater than current prices then update both
                if new_cash_price > current_cash_price and new_exchange_price > current_exchange_price:
                    update_price_in_database(item_id, new_sell_price, new_cash_price, new_exchange_price)
                # If only cash is greater than current price then update item with new cash
                elif new_cash_price > current_cash_price and new_exchange_price <= current_exchange_price:
                    update_price_in_database(item_id, new_sell_price, new_cash_price, current_exchange_price)
                # If only exchange is greater than current price then update item with new exchange
                elif new_cash_price <= current_cash_price and new_exchange_price > current_exchange_price:
                    update_price_in_database(item_id, new_sell_price, current_cash_price, new_exchange_price)
                # Record the new price history
                add_item_to_price_history(item_id, new_sell_price, new_exchange_price, new_cash_price)
            else:
                print(f"Price not found for ID {item_id}")
        else:
            print(f"Failed to fetch data for ID {item_id}")

def generate_report(): 
    
    results = fetch_price_changes()
    
    pd.set_option('display.max_rows', 100)  # Replace 100 with a number larger than your row count

    # Execute the query and load the result into a Pandas DataFrame
    df = pd.DataFrame(results)

    # Print the DataFrame
    print(df)