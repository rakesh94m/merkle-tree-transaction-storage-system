# Merkle Tree Transaction Storage System

A Flask application that stores transactions in SQLite and builds a Merkle tree to verify data integrity. It also generates a proof of inclusion for an individual transaction using only the transaction hash, sibling hashes, and Merkle root.

## Features

- Add and persist transactions in SQLite.
- Build a SHA-256 Merkle tree from the stored transactions.
- Detect changes by comparing the computed tree with the stored tree.
- Generate a Merkle proof for a transaction by its transaction ID.
- Verify a proof without downloading or recalculating the complete tree.
- Use parameterized SQL queries for database operations.

## Requirements

- Python 3.11 or later
- Flask

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run the application

This is a Flask application, so run it with Python:

```powershell
python app.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

Do not run this project with `streamlit run app.py`.

## Using Merkle proofs

Use the **Prove Transaction Inclusion** form on the homepage and enter a transaction ID such as `T1`.

The proof API is also available at:

```text
GET /proof/<transaction_id>
```

Example:

```text
http://127.0.0.1:5000/proof/T1
```

The response contains the transaction, its leaf index, the Merkle root, and the sibling path. Each path entry includes a hash and its position (`left` or `right`). A verifier can call `verify_merkle_proof()` from `merkle_tree_code.py` to validate the transaction against the returned root.

## Project structure

```text
app.py                 Flask routes and web interface
database_functions.py  SQLite database operations
merkle_tree_code.py    SHA-256 and Merkle tree implementation
templates/index.html   Web interface
requirements.txt       Python dependencies
transactions.db        Runtime database created when the app starts
```

## Git commands for future updates

```powershell
git add .
git commit -m "Describe your changes"
git push
```