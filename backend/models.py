from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="sender_user", cascade="all, delete-orphan"
    )


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("tx_id", name="uq_transactions_tx_id"),
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_sender_created", "sender_user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tx_id: Mapped[str] = mapped_column(String(128), nullable=False)
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    sender_user: Mapped[User] = relationship(back_populates="transactions")

    def as_dict(self) -> dict:
        return {
            "tx_id": self.tx_id,
            "sender": self.sender_user.email,
            "receiver": self.receiver,
            "amount": float(self.amount),
            "timestamp": self.created_at.isoformat(),
        }
