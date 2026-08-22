# database_functions.py
import sqlite3
import json

def init_db():
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            tx_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    # Table to store the Merkle tree layers (golden copy)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merkle_tree_store (
            id INTEGER PRIMARY KEY,
            layers TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_all_transactions():
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT tx_id, sender, receiver, amount, timestamp FROM transactions ORDER BY id")
    txs = cursor.fetchall()
    conn.close()
    return ["| ".join(map(str, tx)) for tx in txs]

def get_transaction_by_tx_id(tx_id):
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tx_id, sender, receiver, amount, timestamp "
        "FROM transactions WHERE tx_id = ? ORDER BY id LIMIT 1",
        (tx_id,)
    )
    transaction = cursor.fetchone()
    conn.close()
    return "| ".join(map(str, transaction)) if transaction else None

def insert_transaction_to_db(tx_id, sender, receiver, amount, timestamp):
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (tx_id, sender, receiver, amount, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (tx_id, sender, receiver, amount, timestamp))
    conn.commit()
    conn.close()

def get_stored_layers():
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT layers FROM merkle_tree_store WHERE id = 1")
    stored_layers_json = cursor.fetchone()
    conn.close()
    if stored_layers_json:
        return json.loads(stored_layers_json[0])
    return None

def update_stored_layers(layers_list):
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    layers_json = json.dumps(layers_list)
    cursor.execute("REPLACE INTO merkle_tree_store (id, layers) VALUES (?, ?)", (1, layers_json))
    conn.commit()
    conn.close()