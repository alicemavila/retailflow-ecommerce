"""Registro centralizado dos modelos SQLAlchemy do RetailFlow.

Importar todos os modelos aqui garante que Base.metadata contenha
as nove tabelas e que o Alembic autogenerate detecte todas elas.
"""

from src.app.models.base import Base
from src.app.models.user import User, UserRole
from src.app.models.address import Address
from src.app.models.category import Category
from src.app.models.product import Product
from src.app.models.inventory_movement import InventoryMovement, MovementType
from src.app.models.cart import Cart
from src.app.models.cart_item import CartItem
from src.app.models.order import (
    Order,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from src.app.models.order_item import OrderItem

__all__ = [
    "Base",
    # Modelos e Enums
    "User",
    "UserRole",
    "Address",
    "Category",
    "Product",
    "InventoryMovement",
    "MovementType",
    "Cart",
    "CartItem",
    "Order",
    "OrderStatus",
    "PaymentMethod",
    "PaymentStatus",
    "OrderItem",
]
