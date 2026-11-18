"""Modelo InventoryMovement — histórico de movimentações de estoque."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.order import Order
    from src.app.models.product import Product
    from src.app.models.user import User


class MovementType(str, enum.Enum):
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    SALE = "SALE"
    ORDER_CANCELLATION = "ORDER_CANCELLATION"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"


class InventoryMovement(Base):
    """Tabela de movimentações de estoque — trilha append-only."""

    __tablename__ = "inventory_movements"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # FK para Product — NOT NULL, RESTRICT (não permite excluir produto se houver movimentações)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Quantidade movimentada (positivo = entrada, negativo = saída)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Tipo de movimentação (VARCHAR(30) + CHECK constraint)
    movement_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # FK opcional para o pedido de referência
    reference_order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Motivo ou justificativa da movimentação
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # FK para o usuário responsável pelo registro
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamp de criação imutável
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relacionamentos
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="inventory_movements",
        lazy="raise",
    )
    order: Mapped[Order | None] = relationship(
        "Order",
        back_populates="inventory_movements",
        lazy="raise",
    )
    user: Mapped[User | None] = relationship(
        "User",
        back_populates="inventory_movements",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "movement_type IN ('PURCHASE_RECEIPT', 'SALE', 'ORDER_CANCELLATION', 'MANUAL_ADJUSTMENT')",
            name="ck_inventory_movements_movement_type",
        ),
        CheckConstraint("quantity != 0", name="ck_inventory_movements_quantity_nonzero"),
        Index("ix_inventory_movements_product_id", "product_id"),
        Index("ix_inventory_movements_reference_order_id", "reference_order_id"),
        Index("ix_inventory_movements_user_id", "user_id"),
        Index("ix_inventory_movements_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<InventoryMovement id={self.id} product_id={self.product_id} "
            f"type={self.movement_type} qty={self.quantity}>"
        )
