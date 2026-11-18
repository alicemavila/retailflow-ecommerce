"""Modelo InventoryMovement — histórico de movimentações de estoque."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
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
    PURCHASE = "purchase"       # compra/reposição de estoque
    SALE = "sale"               # venda (saída pelo pedido)
    ADJUSTMENT = "adjustment"   # ajuste manual
    RETURN = "return"           # devolução
    LOSS = "loss"               # perda/quebra


class InventoryMovement(Base):
    """Tabela de movimentações de estoque — somente inserção (append-only)."""

    __tablename__ = "inventory_movements"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # FK para Product — SET NULL para exclusão lógica (produto pode ser marcado DELETED)
    product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )

    # FK opcional para o pedido que originou a movimentação
    order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # FK para usuário responsável pelo registro
    performed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Tipo de movimentação
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, name="movement_type", create_type=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )

    # Quantidade: positivo = entrada, negativo = saída
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Estoque antes e depois da movimentação
    stock_before: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # Referência externa opcional (NF, lote, etc.)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp (somente criação — movimentação é imutável)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relacionamentos
    product: Mapped[Product | None] = relationship(
        "Product",
        back_populates="inventory_movements",
        lazy="raise",
    )
    order: Mapped[Order | None] = relationship(
        "Order",
        back_populates="inventory_movements",
        lazy="raise",
    )
    performed_by_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[performed_by],
        lazy="raise",
    )

    __table_args__ = (
        # Consistência matemática: stock_after = stock_before + quantity
        CheckConstraint(
            "stock_after = stock_before + quantity",
            name="stock_math_consistency",
        ),
        # Estoque nunca pode ser negativo
        CheckConstraint("stock_after >= 0", name="stock_after_non_negative"),
        CheckConstraint("stock_before >= 0", name="stock_before_non_negative"),
        # Índices de busca
        Index("ix_inventory_movements_product_id", "product_id"),
        Index("ix_inventory_movements_order_id", "order_id"),
        Index("ix_inventory_movements_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<InventoryMovement id={self.id} product_id={self.product_id} "
            f"type={self.movement_type} qty={self.quantity}>"
        )
