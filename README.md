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
backend/
  app.py                 application factory and configuration
  models.py              SQLAlchemy User and Transaction models
  routes/api.py          session auth and JSON REST endpoints
  services/crypto.py     canonical JSON, double SHA-256, trees and proofs
  services/anchor.py     signed external Merkle root/layer anchor
frontend/                asynchronous browser client and scalable layout
app.py                   WSGI entry point
docker-compose.yml       backend/frontend orchestration
```

The API uses secure HTTP-only sessions. Register and log in through
`/api/auth/register` and `/api/auth/login`, create transactions at
`/api/transactions`, and request an inclusion proof at `/api/proof/<tx_id>`.

## Local development

Run these commands from the repository root (`C:\Btech\SEM3\PYTHON\Merkle Tree Based Transactions Storage System.worktrees\merkle-tree-app-refactor-structure`):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:SECRET_KEY = "replace-with-a-long-local-secret"
$env:MERKLE_ANCHOR_SECRET = "replace-with-a-long-anchor-secret"
python -m backend.app
```

In a second terminal, serve the frontend:

```powershell
cd frontend
python -m http.server 8000
```

Open `http://127.0.0.1:8000`. If your terminal is inside `backend`, use the
absolute script path instead of relying on the current working directory:

```powershell
python "C:\Btech\SEM3\PYTHON\Merkle Tree Based Transactions Storage System.worktrees\merkle-tree-app-refactor-structure\backend\app.py"
```

For the complete containerized stack:

```powershell
$env:SECRET_KEY = "replace-with-a-long-local-secret"
$env:MERKLE_ANCHOR_SECRET = "replace-with-a-long-anchor-secret"
docker compose up --build
```

Then open `http://127.0.0.1:8080`.

## Git commands for future updates

```powershell
git add .
git commit -m "Describe your changes"
git push
```