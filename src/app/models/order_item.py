"""Modelo OrderItem — itens de cada pedido."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.order import Order
    from src.app.models.product import Product


class OrderItem(Base):
    """Tabela de itens de pedido (8 colunas aprovadas no planejamento)."""

    __tablename__ = "order_items"

    # 1. Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # 2. FK para Order (CASCADE)
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 3. FK para Product — RESTRICT (não permite excluir produto referenciado em pedido)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # 4. Snapshot do nome do produto no momento da compra (VARCHAR(200))
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 5. Snapshot do SKU do produto no momento da compra (VARCHAR(50))
    product_sku: Mapped[str] = mapped_column(String(50), nullable=False)

    # 6. Preço unitário (>= 0.00)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # 7. Quantidade adquirida (> 0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # 8. Subtotal da linha: unit_price * quantity (>= 0.00)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relacionamentos
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="items",
        lazy="raise",
    )
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="order_items",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint("subtotal = unit_price * quantity", name="ck_order_items_subtotal_math"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("subtotal >= 0", name="ck_order_items_subtotal_non_negative"),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem id={self.id} order_id={self.order_id} "
            f"product_id={self.product_id} qty={self.quantity} subtotal={self.subtotal}>"
        )
