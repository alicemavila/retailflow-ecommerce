"""Modelo Product — catálogo de produtos."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
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


class Product(Base):
    """Tabela de produtos do catálogo (12 colunas aprovadas no planejamento)."""

    __tablename__ = "products"

    # 1. Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # 2. Chave Estrangeira para Category (INTEGER, NOT NULL, RESTRICT)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # 3. Nome
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 4. Slug amigável
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True)

    # 5. Descrição
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 6. SKU (código de identificação de estoque)
    sku: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # 7. Valor financeiro: NUMERIC(10,2) (permite >= 0.00 para itens promocionais/gratuitos)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # 8. Quantidade em estoque
    stock_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    # 9. URL da imagem do produto
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 10. Desativação lógica por flag booleana
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    # 11. Data de criação
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # 12. Data de atualização
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relacionamentos
    category: Mapped[Category] = relationship(
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
        CheckConstraint("price >= 0.00", name="ck_products_price_non_negative"),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_non_negative"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} slug={self.slug!r} price={self.price}>"
