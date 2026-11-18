"""Modelo Product — catálogo de produtos."""

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
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.cart_item import CartItem
    from src.app.models.category import Category
    from src.app.models.inventory_movement import InventoryMovement
    from src.app.models.order_item import OrderItem


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"  # exclusão lógica para produtos com histórico de movimentações


class Product(Base):
    """Tabela de produtos do catálogo."""

    __tablename__ = "products"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Chave Estrangeira para Category
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Campos de produto
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    # Valor financeiro: Decimal no Python, NUMERIC(10,2) no PostgreSQL
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    # Estoque
    stock_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    # Status com exclusão lógica
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="product_status", create_type=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=text("'active'"),
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
    category: Mapped[Category | None] = relationship(
        "Category",
        back_populates="products",
        lazy="raise",
    )
    inventory_movements: Mapped[list[InventoryMovement]] = relationship(
        "InventoryMovement",
        back_populates="product",
        lazy="raise",
    )
    cart_items: Mapped[list[CartItem]] = relationship(
        "CartItem",
        back_populates="product",
        lazy="raise",
    )
    order_items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="raise",
    )

    __table_args__ = (
        # Estoque não pode ser negativo
        CheckConstraint("stock_quantity >= 0", name="stock_non_negative"),
        # Preço deve ser positivo
        CheckConstraint("price > 0", name="price_positive"),
        # Índice para busca por categoria
        Index("ix_products_category_id", "category_id"),
        # Índice de status para filtros
        Index("ix_products_status", "status"),
        # slug e sku já possuem UNIQUE — sem índice redundante
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} slug={self.slug!r} price={self.price}>"
