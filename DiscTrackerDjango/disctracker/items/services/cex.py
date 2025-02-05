import requests
import logging
from datetime import datetime

from items.models import Item, PriceHistory

logger = logging.getLogger(__name__)

def fetch_item(cex_id):
    try:
        if not cex_id:
            logger.error("Invalid CEX ID provided: %s", cex_id)
            return None
            
        search_url = f'https://wss2.cex.uk.webuy.io/v3/boxes/{cex_id}/detail'
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()['response']['data']
        
        if not data:
            logger.warning("Fetched item returned no data")
            return None
        
        logger.info("Successfully fetched item with CEX ID %s", cex_id)
        return data
    except requests.exceptions.HTTPError as e:
        logger.exception("HTTP Error when fetching item by CEX ID %s: %s", cex_id, e)
        return None
    except requests.exceptions.JSONDecodeError as e:
        logger.exception("Failed to parse JSON response for CEX ID %s: %s", cex_id, e)
        return None
    except Exception as e:
        logger.exception("An unexpected error occurred for fetching item by CEX ID %s: %s", cex_id, e)
        return None

def create_or_update_item(cex_data):
    if cex_data is None:
        logger.error("Cex data is None, cannot create item")  
        return None
        
    #TODO: Add validation for cex_data    
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
        
    return item

def create_price_history_entry(item):
    if not item:
        logger.error("Item is None, cannot create price history entry")
        return None
    
    #TODO: Validate attributes of item before creating
    
    try:
        price_entry = PriceHistory.objects.create(
            item=item,
            sell_price=item.sell_price,
            exchange_price=item.exchange_price,
            cash_price=item.cash_price,
            date_checked=datetime.now(),
        )
        logger.info("Created price history entry for item %s", item.cex_id)
        return price_entry
    except Exception as e:
        logger.exception("Failed to create price history entry for item %s: %s", item.cex_id, e)
        return None

def check_price_updates():
    try: 
        logger.info("Starting price update check.")
        items = Item.objects.all()

        for item in items:
            if not item.cex_id:
                logger.warning("Item has no cex_id so skipping")
                continue
            
            cex_id = item.cex_id

            current_exchange_price = item.exchange_price
            current_cash_price = item.cash_price

            logger.info("Fetching data for CEX ID: %s", cex_id)

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
                    logger.info("Updating all prices for CEX ID: %s", cex_id)
                elif new_cash_price > current_cash_price and new_exchange_price <= current_exchange_price:
                    item.sell_price = new_sell_price
                    item.cash_price = new_cash_price
                    item.save()
                    logger.info("Updating cash and sell price for CEX ID: %s", cex_id)
                elif new_cash_price <= current_cash_price and new_exchange_price > current_exchange_price:
                    item.sell_price = new_sell_price
                    item.exchange_price = new_exchange_price
                    item.save()
                    logger.info("Updating exchange and sell price for CEX ID: %s", cex_id)

                PriceHistory.objects.create(
                    item=item,
                    sell_price=new_sell_price,
                    exchange_price=new_exchange_price,
                    cash_price=new_cash_price,
                    date_checked=datetime.now(),
                )                
                logger.info("Price history recorded for CEX ID: %s", cex_id)
            else:
                logger.warning("New cash or exchange price is None for CEX ID: %s", cex_id)
        
        logger.info("Price updates completed successfully")    
        return "Price updates completed successfully."
    except requests.exceptions.HTTPError as e:
        logger.exception("HTTP Error when fetching item by CEX ID %s: %s", cex_id, e)
        return None
    except requests.exceptions.JSONDecodeError as e:
        logger.exception("Failed to parse JSON response for CEX ID %s: %s", cex_id, e)
        return None
    except Exception as e:
        logger.exception("An unexpected error occurred for checking item prices: %s", e)
        return None