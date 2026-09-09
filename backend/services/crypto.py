import hashlib
import json
from collections.abc import Iterable


def canonical_json(value: dict) -> bytes:
    """Serialize a transaction deterministically before hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def double_sha256(value: bytes | str) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(hashlib.sha256(payload).digest()).hexdigest()


def transaction_leaf(transaction: dict) -> str:
    return double_sha256(canonical_json(transaction))


def parent_hash(left: str, right: str) -> str:
    return double_sha256(bytes.fromhex(left) + bytes.fromhex(right))


def build_merkle_tree(transactions: Iterable[dict]) -> dict:
    leaves = [transaction_leaf(transaction) for transaction in transactions]
    if not leaves:
        return {"root": None, "layers": []}
    layers = [leaves]
    while len(layers[-1]) > 1:
        current = layers[-1]
        layers.append(
            [
                parent_hash(current[index], current[index + 1] if index + 1 < len(current) else current[index])
                for index in range(0, len(current), 2)
            ]
        )
    return {"root": layers[-1][0], "layers": layers}


def append_leaf(layers: list[list[str]], leaf: str) -> list[list[str]]:
    """Append a leaf and recompute only the ancestors affected by the append."""
    updated = [level[:] for level in layers] if layers else [[]]
    updated[0].append(leaf)
    index = len(updated[0]) - 1
    level = 0
    while len(updated[level]) > 1:
        parent_index = index // 2
        if len(updated) <= level + 1:
            updated.append([])
        current = updated[level]
        sibling_index = index - 1 if index % 2 else index + 1
        sibling = current[sibling_index] if sibling_index < len(current) else current[index]
        value = parent_hash(current[index], sibling) if index % 2 == 0 else parent_hash(sibling, current[index])
        if parent_index < len(updated[level + 1]):
            updated[level + 1][parent_index] = value
        else:
            updated[level + 1].append(value)
        index, level = parent_index, level + 1
    return updated


def build_merkle_proof(transactions: list[dict], transaction_index: int) -> list[dict]:
    tree = build_merkle_tree(transactions)
    if transaction_index < 0 or transaction_index >= len(transactions):
        raise IndexError("transaction_index is outside the tree")
    proof = []
    index = transaction_index
    for layer in tree["layers"][:-1]:
        sibling_index = index - 1 if index % 2 else index + 1
        if sibling_index >= len(layer):
            sibling_index = index
        proof.append({"hash": layer[sibling_index], "position": "left" if sibling_index < index else "right"})
        index //= 2
    return proof


def verify_merkle_proof(transaction: dict, proof: list[dict], merkle_root: str) -> bool:
    current = transaction_leaf(transaction)
    for step in proof:
        current = parent_hash(step["hash"], current) if step["position"] == "left" else parent_hash(current, step["hash"])
    return current == merkle_root
