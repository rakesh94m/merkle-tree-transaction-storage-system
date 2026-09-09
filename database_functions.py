"""Deprecated compatibility helpers backed by SQLAlchemy.

New code should use ``backend.models`` and ``backend.extensions.db`` directly.
"""
from flask import current_app

from backend.extensions import db
from backend.models import Transaction


def init_db():
    db.create_all()


def get_all_transactions():
    rows = db.session.scalars(db.select(Transaction).order_by(Transaction.id)).all()
    return [row.as_dict() for row in rows]


def get_transaction_by_tx_id(tx_id):
    row = db.session.scalar(db.select(Transaction).where(Transaction.tx_id == tx_id))
    return row.as_dict() if row else None


def insert_transaction_to_db(*_args, **_kwargs):
    raise RuntimeError("Use POST /api/transactions; direct transaction insertion is disabled")


def get_stored_layers():
    return None


def update_stored_layers(*_args, **_kwargs):
    raise RuntimeError("Merkle layers are maintained by the external anchor service")
