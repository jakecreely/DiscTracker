import sqlite3

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
    
    cur.execute("UPDATE items SET sell_price = ? AND cash_price = ? AND exchange_price = ? WHERE id = ?", (new_sell_price, new_cash_price, new_exchange_price, item_id))
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