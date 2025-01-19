from datetime import datetime

from sqlalchemy import text
from DiscTracker.db_setup import Session
from DiscTracker.models import Item, PriceHistory

def add_item(item):
    title = item['boxDetails'][0]['boxName']
    cex_id = item['boxDetails'][0]['boxId']
    sell_price = item['boxDetails'][0]['sellPrice']
    exchange_price = item['boxDetails'][0]['exchangePrice']
    cash_price = item['boxDetails'][0]['cashPrice']

    session = Session()

    try:
        new_item = Item(
            title = title,
            cex_id = cex_id,
            sell_price = sell_price,
            exchange_price = exchange_price,
            cash_price = cash_price,
            last_checked = datetime.now()
        )

        session.add(new_item)
        session.commit()

        new_price_history_entry = PriceHistory(
            item_id = new_item.id,
            sell_price = sell_price,
            exchange_price = exchange_price,
            cash_price = cash_price,
            date_checked = datetime.now()
        )

        session.add(new_price_history_entry)
        session.commit()

        print(f"Item ({title}) and price history added successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error adding item: {e}")
    
    finally:
        session.close()

def fetch_items_cex_ids():
    session = Session()

    try:
        items = session.query(Item.cex_id).all()

        item_cex_ids = [item.cex_id for item in items]

        return item_cex_ids

    except Exception as e:
        print(f"Error fetching item cex IDs: {e}")
        return []

    finally:
        session.close()

def update_price_in_database(item_id, new_sell_price, new_cash_price, new_exchange_price):
    session = Session()
    
    try:
        item = session.query(Item).filter(Item.cex_id == item_id).first()

        if item:
            item.cash_price = new_cash_price
            item.exchange_price = new_exchange_price
            item.sell_price = new_sell_price
            session.commit()
        else:
            print(f"Item with cex_id {item_id} not found")
            
    except Exception as e:
        print(f"Error updating item {item_id} price: {e}")
        session.rollback();
        
    finally:
        session.close()
    
def add_item_to_price_history(item_id, sell_price, exchange_price, cash_price):
    session = Session()
    
    try:
        new_price_history_entry = PriceHistory(
            item_id = item_id,
            sell_price = sell_price,
            exchange_price = exchange_price,
            cash_price = cash_price
        )
        
        session.add(new_price_history_entry)
        session.commit()
    
    except Exception as e:
        print(f"Error adding item ({item_id}) to price history: {e}")
        session.rollback()
    
    finally: 
        session.close()
    
def remove_item_by_name(name):
    session = Session()
    
    try:
        deleted_count = session.query(Item).filter(Item.name == name).delete()
        
        if deleted_count > 0:
            print(f"Item with name ({name}) deleted successfully")
        else:
            print(f"No item with name ({name}) found")
        
        session.commit()
        
    except Exception as e:
        print(f"Error deleting item by name {name}: {e}")
        session.rollback()
        
    finally:
        session.close()
        
def remove_item_by_cex_id(id):
    session = Session()
    
    try:
        deleted_count = session.query(Item).filter(Item.cex_id == id).delete()
        
        if deleted_count > 0:
            print(f"Item with cex ID ({id}) deleted successfully")
        else:
            print(f"No item with cex ID ({id}) found")
        
        session.commit()
        
    except Exception as e:
        print(f"Error deleting item by cex ID {id}: {e}")
        session.rollback()
        
    finally:
        session.close()
    
def get_all_items():
    session = Session()
    
    try:
        items = session.query(Item).all()
        
        return items
        
    except Exception as e:
        print(f"Error getting items: {e}")
        return []
        
    finally:
        session.close()

def fetch_price_changes(): 
    session = Session()

    result = session.execute(text('''
    SELECT 
        items.id,
        items.title,
        items.sell_price AS current_sell_value,
        items.cash_price AS current_sell_cash_value,
        items.exchange_price AS current_sell_exchange_value,
        price_history.sell_price AS previous_sell_value,
        price_history.cash_price AS previous_sell_cash_value,
        price_history.exchange_price AS previous_sell_exchange_value,
        price_history.date_checked AS previous_sell_date,
        (items.sell_price - price_history.sell_price) AS sell_value_change,
        (items.cash_price - price_history.cash_price) AS sell_cash_value_change,
        (items.exchange_price - price_history.exchange_price) AS sell_exchange_value_change
    FROM 
        items
    JOIN 
        price_history 
    ON 
        items.id = price_history.item_id
    WHERE 
        price_history.date_checked = (
            SELECT MAX(date_checked) 
            FROM price_history 
            WHERE price_history.item_id = items.id
        );
    '''))
    
    return result
