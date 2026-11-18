"""Modelo Category — categorias de produtos."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.product import Product


class Category(Base):
    """Tabela de categorias de produtos (hierarquia simples via self-join)."""

    __tablename__ = "categories"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Chave Estrangeira para categoria pai (self-join)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Campos
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False, server_default=text("true")
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
    parent: Mapped[Category | None] = relationship(
        "Category",
        back_populates="children",
        remote_side="Category.id",
        lazy="raise",
    )
    children: Mapped[list[Category]] = relationship(
        "Category",
        back_populates="parent",
        lazy="raise",
    )
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
        lazy="raise",
    )

    __table_args__ = (
        # ix em parent_id para hierarquia
        Index("ix_categories_parent_id", "parent_id"),
        # slug já possui UNIQUE acima — não adicionar ix redundante
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} slug={self.slug!r}>"
