"""Registro centralizado dos modelos SQLAlchemy do RetailFlow.

Importar todos os modelos aqui garante que Base.metadata contenha
as nove tabelas e que o Alembic autogenerate detecte todas elas.
"""

from src.app.models.base import Base  # noqa: F401 — expõe Base e metadata
from src.app.models.user import User, UserRole  # noqa: F401
from src.app.models.address import Address  # noqa: F401
from src.app.models.category import Category  # noqa: F401
from src.app.models.product import Product, ProductStatus  # noqa: F401
from src.app.models.inventory_movement import (  # noqa: F401
    InventoryMovement,
    MovementType,
)
from src.app.models.cart import Cart  # noqa: F401
from src.app.models.cart_item import CartItem  # noqa: F401
from src.app.models.order import Order, OrderStatus  # noqa: F401
from src.app.models.order_item import OrderItem  # noqa: F401

__all__ = [
    "Base",
    # Modelos
    "User",
    "UserRole",
    "Address",
    "Category",
    "Product",
    "ProductStatus",
    "InventoryMovement",
    "MovementType",
    "Cart",
    "CartItem",
    "Order",
    "OrderStatus",
    "OrderItem",
]
