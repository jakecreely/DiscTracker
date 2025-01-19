import sqlite3
import pandas as pd

DATABASE_NAME = 'disc_tracker.db'

def initialise_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    cex_id TEXT,
                    sell_price REAL,
                    exchange_price REAL,
                    cash_price, REAL
                    last_checked DATE,
                    previous_exchange_price REAL,
                    previous_cash_price
                 )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    sell_price REAL,
                    exchange_price REAL,
                    cash_price REAL,
                    date_checked DATE DEFAULT (DATE('now')),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                 )''')
    conn.commit()
    conn.close()
    
def add_item(item):
    # check structure - contains title, cex_id, price
    title = item['boxDetails'][0]['boxName']
    cex_id = item['boxDetails'][0]['boxId']
    sell_price = item['boxDetails'][0]['sellPrice']
    exchange_price = item['boxDetails'][0]['exchangePrice']
    cash_price = item['boxDetails'][0]['cashPrice']
    
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute('''
                INSERT INTO items (title, cex_id, sell_price, exchange_price, cash_price)
                VALUES (?, ?, ?, ?, ?)
                ''', (title, cex_id, sell_price, exchange_price, cash_price))
    
    # Get the ID of the newly inserted record
    new_id = cur.lastrowid
    
    # Commit the transaction
    conn.commit()
    
    # Fetch the newly inserted record
    cur.execute('''
            INSERT INTO price_history (item_id, sell_price, exchange_price, cash_price)
            VALUES (?, ?, ?, ?)
            ''', (new_id, sell_price, exchange_price, cash_price))
    
    conn.commit()
    
    
def fetch_item_ids():
    # Retrieve IDs from the database
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    
    cur.execute("SELECT cex_id FROM items")
    ids = cur.fetchall()
    conn.close()
    return [item_id[0] for item_id in ids]

def update_price_in_database(item_id, new_sell_price, new_cash_price, new_exchange_price):
    # Update the database with new price
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    
    print(f"item_id:{item_id}")
    print(f"sell_price:{new_sell_price}")
    print(f"cash_price:{new_cash_price}")
    print(f"exchange_price:{new_exchange_price}")

    
    cur.execute('''
        UPDATE items 
        SET 
            sell_price = ?,
            cash_price = ?,
            exchange_price = ?
        WHERE cex_id = ?
        ''', (new_sell_price, new_cash_price, new_exchange_price, item_id))
    conn.commit()
    conn.close()
    
def add_item_to_price_history(item_id, sell_price, exchange_price, cash_price):
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute('''
            INSERT INTO price_history (item_id, sell_price, exchange_price, cash_price)
            VALUES (?, ?, ?, ?)
            ''', (item_id, sell_price, exchange_price, cash_price))
    conn.commit()
    
def remove_item_by_name(name):
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute('''
                DELETE FROM items
                WHERE name = ?
                ''', (name))
    conn.commit()

def remove_item_by_id(id):
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute('''
                DELETE FROM items
                WHERE id = ?
                ''', (id))
    conn.commit()
    
def get_all_items():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute('''
                SELECT * FROM items
                ''')
    items = cur.fetchall()
    conn.close()
    return items

def fetch_price_changes(): 
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    
    #         //items.last_checked AS current_last_checked_date, 
    
    cur.execute('''
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
    ''')
    
    results = cur.fetchall()
    # Close the database connection
    conn.close()
    return results
