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
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
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
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base):
    """Tabela de pedidos."""

    __tablename__ = "orders"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # FK para User — pedido é preservado se usuário for excluído (SET NULL)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Número de pedido legível (ex: "RF-2024-000001")
    order_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )

    # Status
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", create_type=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=text("'pending'"),
    )

    # Totais financeiros — NUMERIC(10,2)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0.00")
    )
    discount_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0.00")
    )
    grand_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Snapshot do endereço de entrega no momento do pedido (JSONB)
    shipping_address_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relacionamentos
    user: Mapped[User | None] = relationship(
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
        # Consistência financeira: grand_total = subtotal + shipping_cost - discount_total
        CheckConstraint(
            "grand_total = subtotal + shipping_cost - discount_total",
            name="grand_total_math",
        ),
        # Valores não podem ser negativos
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint("shipping_cost >= 0", name="shipping_cost_non_negative"),
        CheckConstraint("discount_total >= 0", name="discount_total_non_negative"),
        CheckConstraint("grand_total >= 0", name="grand_total_non_negative"),
        # Índices
        Index("ix_orders_user_id", "user_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
        # order_number já possui UNIQUE — sem ix redundante
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} number={self.order_number!r} status={self.status}>"
