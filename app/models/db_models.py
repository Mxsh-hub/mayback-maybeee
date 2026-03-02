from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    transaction_ref: Mapped[str] = mapped_column(String(128), nullable=False)

    txn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    direction: Mapped[str] = mapped_column(
        Enum("income", "expense", name="direction_enum"),
        nullable=False,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    classification: Mapped["TransactionClassification | None"] = relationship(
        "TransactionClassification",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "transaction_ref", name="uq_user_transaction_ref"),
        Index("idx_user_date", "user_id", "txn_date"),
    )


class TransactionClassification(Base):
    __tablename__ = "transaction_classifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        Enum("essential", "non_essential", "emergency", name="expense_category_enum"),
        nullable=False,
    )
    intent_label: Mapped[str] = mapped_column(
        Enum("planned", "impulse", "na", name="intent_label_enum"),
        nullable=False,
        default="na",
    )
    essentiality: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    transaction: Mapped[Transaction] = relationship("Transaction", back_populates="classification")
