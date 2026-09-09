"""Compatibility facade for the refactored cryptographic service."""
from backend.services.crypto import build_merkle_tree as _build_tree
from backend.services.crypto import double_sha256


def _legacy_transaction(value: str) -> dict:
    parts = [part.strip() for part in value.split("|")]
    return {"tx_id": parts[0], "sender": parts[1], "receiver": parts[2], "amount": float(parts[3]), "timestamp": parts[4]}


def _normalize(values):
    return [_legacy_transaction(value) if isinstance(value, str) else value for value in values]


def build_merkle_tree(transactions):
    return _build_tree(_normalize(transactions))


def build_merkle_proof(transactions, transaction_index):
    from backend.services.crypto import build_merkle_proof as build
    return build(_normalize(transactions), transaction_index)


def verify_merkle_proof(transaction, proof, merkle_root):
    from backend.services.crypto import verify_merkle_proof
    value = _legacy_transaction(transaction) if isinstance(transaction, str) else transaction
    return verify_merkle_proof(value, proof, merkle_root)
