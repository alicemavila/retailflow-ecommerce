"""Modelo Category — categorias de produtos."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Identity, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.product import Product


class Category(Base):
    """Tabela de categorias de produtos (PK INTEGER IDENTITY, 6 colunas aprovadas)."""

    __tablename__ = "categories"

    # Chave Primária INTEGER IDENTITY (autoincrement)
    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )

    # Campos aprovados
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default=text("true")
    )

    # Timestamp de criação (sem updated_at conforme planejamento consolidado)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relacionamentos
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} slug={self.slug!r}>"
