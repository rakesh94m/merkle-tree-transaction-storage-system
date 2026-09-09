from decimal import Decimal, InvalidOperation
from functools import wraps
from secrets import token_urlsafe

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models import Transaction, User
from backend.services.anchor import RootAnchor
from backend.services.crypto import append_leaf, build_merkle_proof, build_merkle_tree, transaction_leaf

api = Blueprint("api", __name__, url_prefix="/api")
auth = Blueprint("auth", __name__, url_prefix="/api/auth")


def authenticated(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)
    return wrapper


@auth.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email, password = str(data.get("email", "")).strip().lower(), data.get("password", "")
    if "@" not in email or not isinstance(password, str) or len(password) < 12:
        return jsonify({"error": "A valid email and password of at least 12 characters are required"}), 400
    user = User(email=email, password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email is already registered"}), 409
    return jsonify({"user": {"id": user.id, "email": user.email}}), 201


@auth.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = db.session.scalar(db.select(User).where(User.email == str(data.get("email", "")).strip().lower()))
    password = data.get("password", "")
    if not user or not isinstance(password, str) or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return jsonify({"error": "Invalid credentials"}), 401
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"user": {"id": user.id, "email": user.email}})


@auth.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@api.get("/transactions")
@authenticated
def transactions():
    rows = db.session.scalars(
        db.select(Transaction).where(Transaction.sender_user_id == session["user_id"]).order_by(Transaction.id)
    ).all()
    return jsonify({"transactions": [row.as_dict() for row in rows]})


@api.get("/tree")
@authenticated
def tree():
    rows = db.session.scalars(db.select(Transaction).order_by(Transaction.id)).all()
    return jsonify(build_merkle_tree([row.as_dict() for row in rows]))


@api.post("/transactions")
@authenticated
def create_transaction():
    data = request.get_json(silent=True) or {}
    receiver = str(data.get("receiver", "")).strip()
    try:
        amount = Decimal(str(data.get("amount")))
    except (InvalidOperation, TypeError):
        amount = Decimal("0")
    if not receiver or amount <= 0:
        return jsonify({"error": "receiver and a positive amount are required"}), 400
    user = db.session.get(User, session["user_id"])
    row = Transaction(tx_id=token_urlsafe(18), sender_user_id=user.id, receiver=receiver, amount=amount)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Transaction could not be created"}), 409
    rows = db.session.scalars(db.select(Transaction).order_by(Transaction.id)).all()
    anchor = RootAnchor(current_app.config["MERKLE_ANCHOR_PATH"], current_app.config["MERKLE_ANCHOR_SECRET"])
    previous = anchor.load()
    if previous:
        layers = append_leaf(previous["layers"], transaction_leaf(row.as_dict()))
        anchor.save(layers[-1][0], layers)
    else:
        tree = build_merkle_tree([item.as_dict() for item in rows])
        anchor.save(tree["root"], tree["layers"])
    return jsonify({"transaction": row.as_dict()}), 201


@api.get("/proof/<tx_id>")
@authenticated
def proof(tx_id):
    row = db.session.scalar(db.select(Transaction).where(Transaction.tx_id == tx_id))
    if not row or row.sender_user_id != session["user_id"]:
        return jsonify({"error": "Transaction not found"}), 404
    rows = db.session.scalars(db.select(Transaction).order_by(Transaction.id)).all()
    payloads = [item.as_dict() for item in rows]
    index = next(i for i, item in enumerate(rows) if item.tx_id == tx_id)
    tree = build_merkle_tree(payloads)
    return jsonify({"transaction": row.as_dict(), "transaction_index": index, "merkle_root": tree["root"], "proof": build_merkle_proof(payloads, index)})
