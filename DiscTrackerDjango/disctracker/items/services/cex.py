import requests
import logging
from datetime import datetime
from pydantic import ValidationError
from django.db import DatabaseError

from items.models.db_models import Item, PriceHistory
from items.models.pydantic_models import CexItemApiResponseWrapper, CexIdValidator

logger = logging.getLogger(__name__)

CEX_API_BASE_URL = "https://wss2.cex.uk.webuy.io/v3/boxes"

def fetch_item(cex_id):
    try:
        if not cex_id:
            logger.error("CEX ID not provided: %s", cex_id)
            return None
        
        validated_cex_id_input = CexIdValidator(cex_id=cex_id)
        cex_id = validated_cex_id_input.cex_id
            
        search_url = f'{CEX_API_BASE_URL}/{cex_id}/detail'
        response = requests.get(search_url)
        
        if response.status_code == 404:
            logger.warning("CEX with ID %s not found", cex_id)
            return None
        
        response.raise_for_status()
        
        response_json = response.json()
        
        validated_response = CexItemApiResponseWrapper.model_validate_json(response_json)

        box_details = validated_response.response.data
        
        if len(box_details) == 1:
            logger.info("Successfully fetched item with CEX ID %s", cex_id)
            return box_details[0]
        else:
            logger.error("Box Detail contains more than one element (%s)", len(box_details))
            return None
    
    except ValidationError as e:
        logger.exception("Error validating API response", e)
        return None
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
        
    try:
        #TODO: Add validation for cex_data
        logger.info("Extracting data from cex_data")  
        box_details = cex_data["boxDetails"][0]

        cex_id = box_details.get("boxId")
        if not cex_id:
            logger.error("Missing boxId in cex_data")  
            return None
        
        title = box_details.get("boxName")
        sell_price = box_details.get("sellPrice")
        exchange_price = box_details.get("exchangePrice")
        cash_price = box_details.get("cashPrice")

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
            item.title = box_details.get("boxName", item.title)
            item.sell_price = box_details.get("sellPrice", item.sell_price)
            item.exchange_price = box_details.get("exchangePrice", item.exchange_price)
            item.cash_price = box_details.get("cashPrice", item.cash_price)
            item.last_checked = datetime.now()
            item.save()
            logger.info("Updated item %s in database", cex_id)
        else:
            logger.info("Created item %s in database", cex_id)
            
        return item
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return None
    except Exception as e:
        logger.exception("An unexpected error occured: %s", e)
        return None
    
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
    except DatabaseError as e:
        logger.exception("Database error occured: %s", e)
        return None
    except AttributeError as e:
        logger.exception("Missing attributes: %s", e)
        return None
    except Exception as e:
        logger.exception("Failed to create price history entry for item %s: %s", item.cex_id, e)
        return None

def check_price_updates():
    updated_items = []
    
    try: 
        logger.info("Starting price update check.")
        items = Item.objects.all()

        for item in items:
            if not item.cex_id:
                logger.warning("Item has no cex_id so skipping")
                continue
            
            cex_id = item.cex_id

            logger.info("Fetching data for CEX ID: %s", cex_id)

            response = requests.get(f'{CEX_API_BASE_URL}/{cex_id}/detail')
            response.raise_for_status()
            
            data = response.json()['response']['data']
            new_sell_price = data['boxDetails'][0]['sellPrice']
            new_cash_price = data['boxDetails'][0]['cashPrice']
            new_exchange_price = data['boxDetails'][0]['exchangePrice']
            
            if new_cash_price and new_exchange_price is not None:
                if (item.sell_price != new_sell_price or 
                item.exchange_price != new_exchange_price or 
                item.cash_price != new_cash_price):
                    item.sell_price = new_sell_price
                    item.cash_price = new_cash_price
                    item.exchange_price = new_exchange_price
                    item.last_checked = datetime.now()
                    item.save()
                    logger.info("Updating prices for CEX ID: %s", cex_id)    
                        
                    PriceHistory.objects.create(
                        item=item,
                        sell_price=new_sell_price,
                        exchange_price=new_exchange_price,
                        cash_price=new_cash_price,
                        date_checked=datetime.now(),
                    )  
                    logger.info("Price history recorded for CEX ID: %s", cex_id)
                    
                    updated_items.append(item)
                else:
                    logger.info("No price changes for CEX ID: %s, skipping save", cex_id)
            else:
                logger.warning("New cash or exchange price is None for CEX ID: %s", cex_id)
        
        logger.info("Price updates completed successfully")    
        return updated_items
    except requests.exceptions.HTTPError as e:
        logger.exception("HTTP Error when fetching item by CEX ID %s: %s", cex_id, e)
        return None
    except requests.exceptions.JSONDecodeError as e:
        logger.exception("Failed to parse JSON response for CEX ID %s: %s", cex_id, e)
        return None
    except Exception as e:
        logger.exception("An unexpected error occurred for checking item prices: %s", e)
        return None