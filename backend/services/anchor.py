import hashlib
import hmac
import json
from pathlib import Path


class RootAnchor:
    """A separately stored, signed root anchor; transaction rows never contain it."""

    def __init__(self, path: str, secret: str):
        self.path = Path(path)
        self.secret = secret.encode()

    def save(self, root: str | None, layers: list[list[str]]) -> None:
        payload = json.dumps({"root": root, "layers": layers}, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"payload": payload, "signature": signature}), encoding="utf-8")

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        payload = envelope["payload"]
        expected = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, envelope["signature"]):
            raise ValueError("Merkle root anchor signature is invalid")
        return json.loads(payload)
