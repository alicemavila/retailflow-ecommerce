"""align_schema_with_consolidated_spec

Segunda migração incremental: alinha os esquemas das 9 tabelas estritamente
ao Planejamento Técnico Consolidado:

1. User:
   - full_name: VARCHAR(150) NOT NULL.
   - role: VARCHAR(20) com CHECK ('ADMIN', 'CUSTOMER') e default 'CUSTOMER'.
2. Address:
   - number: VARCHAR(50) NOT NULL.
   - zip_code: VARCHAR(20) NOT NULL.
   - Remoção de colunas excedentes: label, recipient_name, country, updated_at (11 colunas).
3. Category:
   - id: alterado de UUID para INTEGER IDENTITY (autoincrement).
   - name: VARCHAR(100) NOT NULL UNIQUE.
   - slug: VARCHAR(120) NOT NULL UNIQUE.
   - Remoção de parent_id e updated_at (6 colunas).
4. Product:
   - category_id: alterado de UUID nullable para INTEGER NOT NULL, FK ON DELETE RESTRICT.
   - name: VARCHAR(200) NOT NULL.
   - slug: VARCHAR(220) NOT NULL UNIQUE.
   - sku: VARCHAR(50) NOT NULL UNIQUE.
   - image_url: VARCHAR(500) NULL.
   - is_active: BOOLEAN NOT NULL DEFAULT true (substitui status enum).
   - price: CHECK (price >= 0.00).
   (12 colunas).
5. CartItem:
   - Remoção de updated_at (5 colunas).
6. InventoryMovement:
   - product_id: NOT NULL, FK ON DELETE RESTRICT.
   - Remoção de stock_before, stock_after, reference, notes.
   - Renomeação conceitual/colunas: order_id -> reference_order_id (SET NULL), performed_by -> user_id (SET NULL), notes -> reason.
   - movement_type: VARCHAR(30) com CHECK ('PURCHASE_RECEIPT', 'SALE', 'ORDER_CANCELLATION', 'MANUAL_ADJUSTMENT').
   - quantity: CHECK (quantity != 0).
   (8 colunas).
7. Order:
   - user_id: NOT NULL, FK ON DELETE RESTRICT.
   - order_code: VARCHAR(20) NOT NULL UNIQUE.
   - idempotency_key: VARCHAR(64) NULL com UNIQUE(user_id, idempotency_key).
   - shipping_address_snapshot: JSONB NOT NULL sem default.
   - payment_method: VARCHAR(30) NOT NULL sem default com CHECK ('SIMULATED_CARD', 'SIMULATED_PIX', 'SIMULATED_BOLETO').
   - payment_status: VARCHAR(30) NOT NULL DEFAULT 'PENDING' com CHECK ('PENDING', 'APPROVED', 'REJECTED').
   - status: VARCHAR(30) NOT NULL DEFAULT 'PENDING' com CHECK ('PENDING', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED').
   - total_amount: CHECK (total_amount = subtotal + shipping_fee).
   - card_brand: VARCHAR(20) NULL, card_last_four: VARCHAR(4) NULL.
   - Remoção de order_number, shipping_cost, discount_total, grand_total.
   (15 colunas).
8. OrderItem:
   - product_id: NOT NULL, FK ON DELETE RESTRICT.
   - product_name: VARCHAR(200) NOT NULL.
   - product_sku: VARCHAR(50) NOT NULL.
   - subtotal: NUMERIC(10,2) NOT NULL, CHECK (subtotal >= 0), CHECK (subtotal = unit_price * quantity).
   - unit_price: CHECK (unit_price >= 0).
   - Remoção de UNIQUE(order_id, product_id).
   - Remoção de created_at, product_name_snapshot, line_total.
   (8 colunas).
9. Remoção de tipos ENUM nativos obsoletos do PostgreSQL.

Revision ID: 48bea4d188e1
Revises: afe5f37774e5
Create Date: 2026-11-18 18:09:56.833459
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '48bea4d188e1'
down_revision: Union[str, None] = 'afe5f37774e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. USERS: full_name VARCHAR(150), role VARCHAR(20) + CHECK
    # -------------------------------------------------------------------------
    op.alter_column(
        'users',
        'full_name',
        existing_type=sa.String(length=255),
        type_=sa.String(length=150),
        existing_nullable=False,
    )
    op.alter_column(
        'users',
        'role',
        existing_type=postgresql.ENUM('customer', 'admin', name='user_role'),
        type_=sa.String(length=20),
        existing_nullable=False,
        server_default=sa.text("'CUSTOMER'"),
        postgresql_using="UPPER(role::text)",
    )
    op.create_check_constraint(
        'ck_users_role',
        'users',
        "role IN ('ADMIN', 'CUSTOMER')",
    )

    # -------------------------------------------------------------------------
    # 2. ADDRESSES: number VARCHAR(50), zip_code VARCHAR(20), remover colunas excedentes
    # -------------------------------------------------------------------------
    op.drop_column('addresses', 'label')
    op.drop_column('addresses', 'recipient_name')
    op.drop_column('addresses', 'country')
    op.drop_column('addresses', 'updated_at')

    op.alter_column(
        'addresses',
        'number',
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        'addresses',
        'zip_code',
        existing_type=sa.String(length=10),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

    # -------------------------------------------------------------------------
    # 3. CATEGORIES & PRODUCTS: migração de UUID para INTEGER IDENTITY
    # -------------------------------------------------------------------------
    # a) Desvincular products.category_id antes de alterar categories.id
    op.drop_constraint(op.f('fk_products_category_id_categories'), 'products', type_='foreignkey')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_column('products', 'category_id')

    # b) Ajustar categories: remover parent_id, updated_at e alterar PK para INTEGER IDENTITY
    op.drop_index(op.f('ix_categories_parent_id'), table_name='categories')
    op.drop_constraint(op.f('fk_categories_parent_id_categories'), 'categories', type_='foreignkey')
    op.drop_column('categories', 'parent_id')
    op.drop_column('categories', 'updated_at')

    op.drop_constraint(op.f('pk_categories'), 'categories', type_='primary')
    op.drop_column('categories', 'id')
    op.add_column(
        'categories',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
    )
    op.create_primary_key(op.f('pk_categories'), 'categories', ['id'])

    op.alter_column(
        'categories',
        'name',
        existing_type=sa.String(length=150),
        type_=sa.String(length=100),
        existing_nullable=False,
    )
    op.create_unique_constraint(op.f('uq_categories_name'), 'categories', ['name'])

    op.alter_column(
        'categories',
        'slug',
        existing_type=sa.String(length=180),
        type_=sa.String(length=120),
        existing_nullable=False,
    )

    # c) Recriar products.category_id como INTEGER NOT NULL com FK ON DELETE RESTRICT
    op.add_column('products', sa.Column('category_id', sa.Integer(), nullable=False))
    op.create_foreign_key(
        op.f('fk_products_category_id_categories'),
        'products', 'categories', ['category_id'], ['id'], ondelete='RESTRICT',
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    # -------------------------------------------------------------------------
    # 4. PRODUCTS: campos restantes, tipos, checks e índices
    # -------------------------------------------------------------------------
    op.alter_column(
        'products',
        'name',
        existing_type=sa.String(length=255),
        type_=sa.String(length=200),
        existing_nullable=False,
    )
    op.alter_column(
        'products',
        'slug',
        existing_type=sa.String(length=300),
        type_=sa.String(length=220),
        existing_nullable=False,
    )
    op.alter_column(
        'products',
        'sku',
        existing_type=sa.String(length=100),
        type_=sa.String(length=50),
        nullable=False,
    )

    op.drop_constraint(op.f('ck_products_price_positive'), 'products', type_='check')
    op.create_check_constraint('ck_products_price_non_negative', 'products', 'price >= 0.00')

    op.drop_index(op.f('ix_products_status'), table_name='products')
    op.drop_column('products', 'status')
    op.add_column(
        'products',
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )
    op.add_column(
        'products',
        sa.Column('image_url', sa.String(length=500), nullable=True),
    )
    op.create_index('ix_products_is_active', 'products', ['is_active'], unique=False)

    # -------------------------------------------------------------------------
    # 5. CART_ITEMS: remover updated_at (manter 5 colunas)
    # -------------------------------------------------------------------------
    op.drop_column('cart_items', 'updated_at')

    # -------------------------------------------------------------------------
    # 6. INVENTORY_MOVEMENTS: alinhar product_id NOT NULL RESTRICT, colunas e checks
    # -------------------------------------------------------------------------
    op.drop_constraint(op.f('ck_inventory_movements_stock_math_consistency'), 'inventory_movements', type_='check')
    op.drop_constraint(op.f('ck_inventory_movements_stock_after_non_negative'), 'inventory_movements', type_='check')
    op.drop_constraint(op.f('ck_inventory_movements_stock_before_non_negative'), 'inventory_movements', type_='check')

    op.drop_constraint(op.f('fk_inventory_movements_order_id_orders'), 'inventory_movements', type_='foreignkey')
    op.drop_constraint(op.f('fk_inventory_movements_performed_by_users'), 'inventory_movements', type_='foreignkey')
    op.drop_index(op.f('ix_inventory_movements_order_id'), table_name='inventory_movements')

    op.drop_column('inventory_movements', 'stock_before')
    op.drop_column('inventory_movements', 'stock_after')
    op.drop_column('inventory_movements', 'reference')
    op.drop_column('inventory_movements', 'notes')
    op.drop_column('inventory_movements', 'order_id')
    op.drop_column('inventory_movements', 'performed_by')

    # product_id alterado para NOT NULL com ON DELETE RESTRICT
    op.drop_constraint(op.f('fk_inventory_movements_product_id_products'), 'inventory_movements', type_='foreignkey')
    op.alter_column('inventory_movements', 'product_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key(
        op.f('fk_inventory_movements_product_id_products'),
        'inventory_movements', 'products', ['product_id'], ['id'], ondelete='RESTRICT',
    )

    op.add_column('inventory_movements', sa.Column('reference_order_id', sa.UUID(), nullable=True))
    op.add_column('inventory_movements', sa.Column('reason', sa.String(length=255), nullable=True))
    op.add_column('inventory_movements', sa.Column('user_id', sa.UUID(), nullable=True))

    op.alter_column(
        'inventory_movements',
        'movement_type',
        existing_type=postgresql.ENUM('purchase', 'sale', 'adjustment', 'return', 'loss', name='movement_type'),
        type_=sa.String(length=30),
        existing_nullable=False,
        postgresql_using="UPPER(movement_type::text)",
    )

    op.create_foreign_key(
        op.f('fk_inventory_movements_reference_order_id_orders'),
        'inventory_movements', 'orders', ['reference_order_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        op.f('fk_inventory_movements_user_id_users'),
        'inventory_movements', 'users', ['user_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index('ix_inventory_movements_reference_order_id', 'inventory_movements', ['reference_order_id'], unique=False)
    op.create_index('ix_inventory_movements_user_id', 'inventory_movements', ['user_id'], unique=False)

    op.create_check_constraint(
        'ck_inventory_movements_movement_type',
        'inventory_movements',
        "movement_type IN ('PURCHASE_RECEIPT', 'SALE', 'ORDER_CANCELLATION', 'MANUAL_ADJUSTMENT')",
    )
    op.create_check_constraint(
        'ck_inventory_movements_quantity_nonzero',
        'inventory_movements',
        'quantity != 0',
    )

    # -------------------------------------------------------------------------
    # 7. ORDERS: user_id NOT NULL RESTRICT, shipping_address_snapshot sem default,
    #            order_code, idempotency_key, pagamentos simulados e checks
    # -------------------------------------------------------------------------
    op.drop_constraint(op.f('ck_orders_grand_total_math'), 'orders', type_='check')
    op.drop_constraint(op.f('ck_orders_grand_total_non_negative'), 'orders', type_='check')
    op.drop_constraint(op.f('ck_orders_discount_total_non_negative'), 'orders', type_='check')
    op.drop_constraint(op.f('ck_orders_shipping_cost_non_negative'), 'orders', type_='check')

    op.drop_constraint(op.f('uq_orders_order_number'), 'orders', type_='unique')
    op.drop_column('orders', 'order_number')
    op.drop_column('orders', 'shipping_cost')
    op.drop_column('orders', 'discount_total')
    op.drop_column('orders', 'grand_total')

    # user_id alterado para NOT NULL com ON DELETE RESTRICT
    op.drop_constraint(op.f('fk_orders_user_id_users'), 'orders', type_='foreignkey')
    op.alter_column('orders', 'user_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key(
        op.f('fk_orders_user_id_users'),
        'orders', 'users', ['user_id'], ['id'], ondelete='RESTRICT',
    )

    # shipping_address_snapshot: remover server_default
    op.alter_column(
        'orders',
        'shipping_address_snapshot',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=None,
        existing_nullable=False,
    )

    op.add_column('orders', sa.Column('order_code', sa.String(length=20), nullable=False))
    op.add_column('orders', sa.Column('idempotency_key', sa.String(length=64), nullable=True))
    op.add_column('orders', sa.Column('shipping_fee', sa.Numeric(precision=10, scale=2), server_default=sa.text('0.00'), nullable=False))
    op.add_column('orders', sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False))
    op.add_column('orders', sa.Column('payment_method', sa.String(length=30), nullable=False))
    op.add_column('orders', sa.Column('payment_status', sa.String(length=30), server_default=sa.text("'PENDING'"), nullable=False))
    op.add_column('orders', sa.Column('card_brand', sa.String(length=20), nullable=True))
    op.add_column('orders', sa.Column('card_last_four', sa.String(length=4), nullable=True))

    op.alter_column(
        'orders',
        'status',
        existing_type=postgresql.ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', name='order_status'),
        type_=sa.String(length=30),
        existing_nullable=False,
        server_default=sa.text("'PENDING'"),
        postgresql_using="UPPER(status::text)",
    )

    op.create_unique_constraint(op.f('uq_orders_order_code'), 'orders', ['order_code'])
    op.create_unique_constraint('uq_orders_user_idempotency_key', 'orders', ['user_id', 'idempotency_key'])

    op.create_check_constraint(
        'ck_orders_total_amount_math',
        'orders',
        'total_amount = subtotal + shipping_fee',
    )
    op.create_check_constraint('ck_orders_shipping_fee_non_negative', 'orders', 'shipping_fee >= 0')
    op.create_check_constraint('ck_orders_total_amount_non_negative', 'orders', 'total_amount >= 0')
    op.create_check_constraint(
        'ck_orders_status',
        'orders',
        "status IN ('PENDING', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')",
    )
    op.create_check_constraint(
        'ck_orders_payment_method',
        'orders',
        "payment_method IN ('SIMULATED_CARD', 'SIMULATED_PIX', 'SIMULATED_BOLETO')",
    )
    op.create_check_constraint(
        'ck_orders_payment_status',
        'orders',
        "payment_status IN ('PENDING', 'APPROVED', 'REJECTED')",
    )

    # -------------------------------------------------------------------------
    # 8. ORDER_ITEMS: product_id NOT NULL RESTRICT, remover uq_order_items,
    #                 remover created_at, ajustar subtotal e checks (8 colunas)
    # -------------------------------------------------------------------------
    op.drop_constraint('uq_order_items_order_id_product_id', 'order_items', type_='unique')
    op.drop_constraint(op.f('ck_order_items_line_total_math'), 'order_items', type_='check')
    op.drop_constraint(op.f('ck_order_items_line_total_positive'), 'order_items', type_='check')
    op.drop_constraint(op.f('ck_order_items_unit_price_positive'), 'order_items', type_='check')

    op.drop_column('order_items', 'product_name_snapshot')
    op.drop_column('order_items', 'line_total')
    op.drop_column('order_items', 'created_at')

    # product_id alterado para NOT NULL com ON DELETE RESTRICT
    op.drop_constraint(op.f('fk_order_items_product_id_products'), 'order_items', type_='foreignkey')
    op.alter_column('order_items', 'product_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key(
        op.f('fk_order_items_product_id_products'),
        'order_items', 'products', ['product_id'], ['id'], ondelete='RESTRICT',
    )

    op.add_column('order_items', sa.Column('product_name', sa.String(length=200), nullable=False))
    op.add_column('order_items', sa.Column('product_sku', sa.String(length=50), nullable=False))
    op.add_column('order_items', sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False))

    op.create_check_constraint(
        'ck_order_items_subtotal_math',
        'order_items',
        'subtotal = unit_price * quantity',
    )
    op.create_check_constraint('ck_order_items_unit_price_non_negative', 'order_items', 'unit_price >= 0')
    op.create_check_constraint('ck_order_items_subtotal_non_negative', 'order_items', 'subtotal >= 0')

    # -------------------------------------------------------------------------
    # 9. REMOÇÃO DOS ENUMS NATIVOS DO POSTGRESQL (NÃO MAIS UTILIZADOS)
    # -------------------------------------------------------------------------
    sa.Enum(name='movement_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='order_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='product_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # Recriação dos ENUMs nativos
    movement_type_enum = sa.Enum('purchase', 'sale', 'adjustment', 'return', 'loss', name='movement_type')
    order_status_enum = sa.Enum('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', name='order_status')
    product_status_enum = sa.Enum('active', 'inactive', 'deleted', name='product_status')
    user_role_enum = sa.Enum('customer', 'admin', name='user_role')

    movement_type_enum.create(op.get_bind(), checkfirst=True)
    order_status_enum.create(op.get_bind(), checkfirst=True)
    product_status_enum.create(op.get_bind(), checkfirst=True)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Reversão OrderItems
    op.drop_constraint('ck_order_items_subtotal_non_negative', 'order_items', type_='check')
    op.drop_constraint('ck_order_items_unit_price_non_negative', 'order_items', type_='check')
    op.drop_constraint('ck_order_items_subtotal_math', 'order_items', type_='check')
    op.drop_column('order_items', 'subtotal')
    op.drop_column('order_items', 'product_sku')
    op.drop_column('order_items', 'product_name')

    op.drop_constraint(op.f('fk_order_items_product_id_products'), 'order_items', type_='foreignkey')
    op.alter_column('order_items', 'product_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key(op.f('fk_order_items_product_id_products'), 'order_items', 'products', ['product_id'], ['id'], ondelete='SET NULL')

    op.add_column('order_items', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('order_items', sa.Column('line_total', sa.NUMERIC(precision=10, scale=2), nullable=False))
    op.add_column('order_items', sa.Column('product_name_snapshot', sa.VARCHAR(length=255), nullable=False))
    op.create_check_constraint(op.f('ck_order_items_unit_price_positive'), 'order_items', 'unit_price > 0')
    op.create_check_constraint(op.f('ck_order_items_line_total_positive'), 'order_items', 'line_total > 0')
    op.create_check_constraint(op.f('ck_order_items_line_total_math'), 'order_items', 'line_total = unit_price * quantity')
    op.create_unique_constraint('uq_order_items_order_id_product_id', 'order_items', ['order_id', 'product_id'])

    # Reversão Orders
    op.drop_constraint('ck_orders_payment_status', 'orders', type_='check')
    op.drop_constraint('ck_orders_payment_method', 'orders', type_='check')
    op.drop_constraint('ck_orders_status', 'orders', type_='check')
    op.drop_constraint('ck_orders_total_amount_non_negative', 'orders', type_='check')
    op.drop_constraint('ck_orders_shipping_fee_non_negative', 'orders', type_='check')
    op.drop_constraint('ck_orders_total_amount_math', 'orders', type_='check')
    op.drop_constraint('uq_orders_user_idempotency_key', 'orders', type_='unique')
    op.drop_constraint(op.f('uq_orders_order_code'), 'orders', type_='unique')
    op.drop_column('orders', 'card_last_four')
    op.drop_column('orders', 'card_brand')
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'payment_method')
    op.drop_column('orders', 'total_amount')
    op.drop_column('orders', 'shipping_fee')
    op.drop_column('orders', 'idempotency_key')
    op.drop_column('orders', 'order_code')

    op.alter_column(
        'orders',
        'shipping_address_snapshot',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=sa.text("'{}'::jsonb"),
        existing_nullable=False,
    )
    op.drop_constraint(op.f('fk_orders_user_id_users'), 'orders', type_='foreignkey')
    op.alter_column('orders', 'user_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key(op.f('fk_orders_user_id_users'), 'orders', 'users', ['user_id'], ['id'], ondelete='SET NULL')

    op.alter_column('orders', 'status',
        existing_type=sa.String(length=30),
        type_=order_status_enum,
        existing_nullable=False,
        server_default=sa.text("'pending'::order_status"),
        postgresql_using="LOWER(status)::order_status",
    )
    op.add_column('orders', sa.Column('grand_total', sa.NUMERIC(precision=10, scale=2), nullable=False))
    op.add_column('orders', sa.Column('discount_total', sa.NUMERIC(precision=10, scale=2), server_default=sa.text('0.00'), nullable=False))
    op.add_column('orders', sa.Column('shipping_cost', sa.NUMERIC(precision=10, scale=2), server_default=sa.text('0.00'), nullable=False))
    op.add_column('orders', sa.Column('order_number', sa.VARCHAR(length=50), nullable=False))
    op.create_unique_constraint(op.f('uq_orders_order_number'), 'orders', ['order_number'])
    op.create_check_constraint(op.f('ck_orders_grand_total_math'), 'orders', 'grand_total = subtotal + shipping_cost - discount_total')
    op.create_check_constraint(op.f('ck_orders_shipping_cost_non_negative'), 'orders', 'shipping_cost >= 0')
    op.create_check_constraint(op.f('ck_orders_discount_total_non_negative'), 'orders', 'discount_total >= 0')
    op.create_check_constraint(op.f('ck_orders_grand_total_non_negative'), 'orders', 'grand_total >= 0')

    # Reversão InventoryMovements
    op.drop_constraint('ck_inventory_movements_quantity_nonzero', 'inventory_movements', type_='check')
    op.drop_constraint('ck_inventory_movements_movement_type', 'inventory_movements', type_='check')
    op.drop_index('ix_inventory_movements_user_id', table_name='inventory_movements')
    op.drop_index('ix_inventory_movements_reference_order_id', table_name='inventory_movements')
    op.drop_constraint(op.f('fk_inventory_movements_user_id_users'), 'inventory_movements', type_='foreignkey')
    op.drop_constraint(op.f('fk_inventory_movements_reference_order_id_orders'), 'inventory_movements', type_='foreignkey')
    op.alter_column('inventory_movements', 'movement_type',
        existing_type=sa.String(length=30),
        type_=movement_type_enum,
        existing_nullable=False,
        postgresql_using="LOWER(movement_type)::movement_type",
    )
    op.drop_column('inventory_movements', 'user_id')
    op.drop_column('inventory_movements', 'reason')
    op.drop_column('inventory_movements', 'reference_order_id')

    op.drop_constraint(op.f('fk_inventory_movements_product_id_products'), 'inventory_movements', type_='foreignkey')
    op.alter_column('inventory_movements', 'product_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key(op.f('fk_inventory_movements_product_id_products'), 'inventory_movements', 'products', ['product_id'], ['id'], ondelete='SET NULL')

    op.add_column('inventory_movements', sa.Column('performed_by', sa.UUID(), nullable=True))
    op.add_column('inventory_movements', sa.Column('order_id', sa.UUID(), nullable=True))
    op.add_column('inventory_movements', sa.Column('notes', sa.TEXT(), nullable=True))
    op.add_column('inventory_movements', sa.Column('reference', sa.VARCHAR(length=255), nullable=True))
    op.add_column('inventory_movements', sa.Column('stock_after', sa.INTEGER(), nullable=False))
    op.add_column('inventory_movements', sa.Column('stock_before', sa.INTEGER(), nullable=False))
    op.create_index(op.f('ix_inventory_movements_order_id'), 'inventory_movements', ['order_id'], unique=False)
    op.create_foreign_key(op.f('fk_inventory_movements_performed_by_users'), 'inventory_movements', 'users', ['performed_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_inventory_movements_order_id_orders'), 'inventory_movements', 'orders', ['order_id'], ['id'], ondelete='SET NULL')
    op.create_check_constraint(op.f('ck_inventory_movements_stock_before_non_negative'), 'inventory_movements', 'stock_before >= 0')
    op.create_check_constraint(op.f('ck_inventory_movements_stock_after_non_negative'), 'inventory_movements', 'stock_after >= 0')
    op.create_check_constraint(op.f('ck_inventory_movements_stock_math_consistency'), 'inventory_movements', 'stock_after = stock_before + quantity')

    # Reversão CartItems
    op.add_column('cart_items', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Reversão Products
    op.drop_index('ix_products_is_active', table_name='products')
    op.drop_column('products', 'image_url')
    op.drop_column('products', 'is_active')
    op.add_column('products', sa.Column('status', product_status_enum, server_default=sa.text("'active'::product_status"), nullable=False))
    op.create_index(op.f('ix_products_status'), 'products', ['status'], unique=False)
    op.drop_constraint('ck_products_price_non_negative', 'products', type_='check')
    op.create_check_constraint(op.f('ck_products_price_positive'), 'products', 'price > 0')

    op.alter_column('products', 'sku', existing_type=sa.String(length=50), type_=sa.String(length=100), nullable=True)
    op.alter_column('products', 'slug', existing_type=sa.String(length=220), type_=sa.String(length=300), existing_nullable=False)
    op.alter_column('products', 'name', existing_type=sa.String(length=200), type_=sa.String(length=255), existing_nullable=False)

    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_constraint(op.f('fk_products_category_id_categories'), 'products', type_='foreignkey')
    op.drop_column('products', 'category_id')

    # Reversão Categories
    op.alter_column('categories', 'slug', existing_type=sa.String(length=120), type_=sa.String(length=180), existing_nullable=False)
    op.drop_constraint(op.f('uq_categories_name'), 'categories', type_='unique')
    op.alter_column('categories', 'name', existing_type=sa.String(length=100), type_=sa.String(length=150), existing_nullable=False)

    op.drop_constraint(op.f('pk_categories'), 'categories', type_='primary')
    op.drop_column('categories', 'id')
    op.add_column('categories', sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.create_primary_key(op.f('pk_categories'), 'categories', ['id'])

    op.add_column('categories', sa.Column('parent_id', sa.UUID(), nullable=True))
    op.add_column('categories', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.create_foreign_key(op.f('fk_categories_parent_id_categories'), 'categories', 'categories', ['parent_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)

    # Re-adicionar category_id UUID em products
    op.add_column('products', sa.Column('category_id', sa.UUID(), nullable=True))
    op.create_foreign_key(op.f('fk_products_category_id_categories'), 'products', 'categories', ['category_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    # Reversão Addresses
    op.alter_column('addresses', 'zip_code', existing_type=sa.String(length=20), type_=sa.String(length=10), existing_nullable=False)
    op.alter_column('addresses', 'number', existing_type=sa.String(length=50), type_=sa.String(length=20), existing_nullable=False)
    op.add_column('addresses', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('addresses', sa.Column('country', sa.VARCHAR(length=3), server_default=sa.text("'BRA'"), nullable=False))
    op.add_column('addresses', sa.Column('recipient_name', sa.VARCHAR(length=255), nullable=False))
    op.add_column('addresses', sa.Column('label', sa.VARCHAR(length=100), nullable=True))

    # Reversão Users
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.alter_column('users', 'role',
        existing_type=sa.String(length=20),
        type_=user_role_enum,
        existing_nullable=False,
        server_default=sa.text("'customer'::user_role"),
        postgresql_using="LOWER(role)::user_role",
    )
    op.alter_column('users', 'full_name', existing_type=sa.String(length=150), type_=sa.String(length=255), existing_nullable=False)
