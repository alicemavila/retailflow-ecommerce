"""Modelo User — usuário da plataforma RetailFlow."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
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
    from src.app.models.order import Order


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


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
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Papel e estado
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=text("'customer'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
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

    # Índice único funcional em LOWER(email) — evita duplicidade case-insensitive
    __table_args__ = (
        Index(
            "ix_users_email_lower",
            func.lower(email),  # type: ignore[arg-type]
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
