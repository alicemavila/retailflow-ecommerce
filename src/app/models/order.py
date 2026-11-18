"""Modelo Order — pedidos de compra."""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.inventory_movement import InventoryMovement
    from src.app.models.order_item import OrderItem
    from src.app.models.user import User


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    SIMULATED_CARD = "SIMULATED_CARD"
    SIMULATED_PIX = "SIMULATED_PIX"
    SIMULATED_BOLETO = "SIMULATED_BOLETO"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Order(Base):
    """Tabela de pedidos (15 colunas aprovadas no planejamento)."""

    __tablename__ = "orders"

    # 1. Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # 2. Código legível do pedido (ex: "ORD-20241118-0001")
    order_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )

    # 3. Chave de idempotência por usuário
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    # 4. FK para User — NOT NULL, RESTRICT (não permite excluir usuário se houver pedidos)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # 5. Status do pedido (VARCHAR(30) + CHECK)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=OrderStatus.PENDING.value,
        server_default=text("'PENDING'"),
    )

    # 6. Subtotal dos itens
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # 7. Taxa de frete
    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )

    # 8. Valor total: subtotal + shipping_fee
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # 9. Snapshot do endereço de entrega no momento do pedido (JSONB, sem default, fornecimento explícito)
    shipping_address_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )

    # 10. Método de pagamento simulado (sem valor padrão arbitrário)
    payment_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # 11. Status do pagamento (distinto do status do pedido)
    payment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PaymentStatus.PENDING.value,
        server_default=text("'PENDING'"),
    )

    # 12. Bandeira do cartão (VARCHAR(20))
    card_brand: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # 13. Últimos quatro dígitos do cartão
    card_last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # 14. Data de criação
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # 15. Data de atualização
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relacionamentos
    user: Mapped[User] = relationship(
        "User",
        back_populates="orders",
        lazy="raise",
    )
    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    inventory_movements: Mapped[list[InventoryMovement]] = relationship(
        "InventoryMovement",
        back_populates="order",
        lazy="raise",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_orders_user_idempotency_key"),
        CheckConstraint(
            "total_amount = subtotal + shipping_fee",
            name="ck_orders_total_amount_math",
        ),
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        CheckConstraint("shipping_fee >= 0", name="ck_orders_shipping_fee_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
        CheckConstraint(
            "status IN ('PENDING', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')",
            name="ck_orders_status",
        ),
        CheckConstraint(
            "payment_method IN ('SIMULATED_CARD', 'SIMULATED_PIX', 'SIMULATED_BOLETO')",
            name="ck_orders_payment_method",
        ),
        CheckConstraint(
            "payment_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_orders_payment_status",
        ),
        Index("ix_orders_user_id", "user_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} code={self.order_code!r} status={self.status}>"
