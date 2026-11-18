"""Modelo User — usuário da plataforma RetailFlow."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.address import Address
    from src.app.models.cart import Cart
    from src.app.models.inventory_movement import InventoryMovement
    from src.app.models.order import Order


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


class User(Base):
    """Tabela de usuários da aplicação."""

    __tablename__ = "users"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Dados de identidade
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    # Papel e estado (VARCHAR(20) + CHECK constraint)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.CUSTOMER.value,
        server_default=text("'CUSTOMER'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
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

    # Relacionamentos (lazy="raise" para segurança async)
    addresses: Mapped[list[Address]] = relationship(
        "Address",
        back_populates="user",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    cart: Mapped[Cart | None] = relationship(
        "Cart",
        back_populates="user",
        lazy="raise",
        uselist=False,
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="user",
        lazy="raise",
    )
    inventory_movements: Mapped[list[InventoryMovement]] = relationship(
        "InventoryMovement",
        back_populates="user",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'CUSTOMER')", name="ck_users_role"),
        Index("ix_users_email_lower", func.lower(email), unique=True),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
