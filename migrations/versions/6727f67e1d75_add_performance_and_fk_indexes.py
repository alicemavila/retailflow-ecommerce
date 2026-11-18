"""add_performance_and_fk_indexes

Terceira migração incremental: adiciona os 4 índices pontuais de chave estrangeira
e consulta identificados na auditoria técnica:

1. addresses.zip_code: otimização de cálculo de frete e consultas logísticas por CEP.
2. cart_items.product_id: otimização de consultas e verificações FK no carrinho (o índice
   composto uq_cart_items_cart_id_product_id atende apenas prefixo cart_id).
3. order_items.order_id: otimização de busca de itens por pedido (necessário após remoção
   do índice composto uq_order_items_order_id_product_id).
4. order_items.product_id: otimização de consultas por produto e verificações de integridade FK.

Revision ID: 6727f67e1d75
Revises: 48bea4d188e1
Create Date: 2026-11-18 20:00:05.331194
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6727f67e1d75'
down_revision: Union[str, None] = '48bea4d188e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. addresses.zip_code (consultas logísticas / CEP)
    op.create_index('ix_addresses_zip_code', 'addresses', ['zip_code'], unique=False)

    # 2. cart_items.product_id (verificações FK de produto no carrinho)
    op.create_index('ix_cart_items_product_id', 'cart_items', ['product_id'], unique=False)

    # 3. order_items.order_id (busca de itens por pedido — ON DELETE CASCADE)
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'], unique=False)

    # 4. order_items.product_id (consultas de vendas e integridade FK — ON DELETE RESTRICT)
    op.create_index('ix_order_items_product_id', 'order_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_order_items_product_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_index('ix_cart_items_product_id', table_name='cart_items')
    op.drop_index('ix_addresses_zip_code', table_name='addresses')
