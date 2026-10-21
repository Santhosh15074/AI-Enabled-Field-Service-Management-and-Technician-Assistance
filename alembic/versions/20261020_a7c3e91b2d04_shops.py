"""shops

Every user, and every knowledge-base entry, now belongs to a shop. Whatever is already in the
database is moved into one shop called "Default shop" (slug "default"), so an existing install
keeps working exactly as before — it just becomes that shop.

Revision ID: a7c3e91b2d04
Revises: d283495802c2
Create Date: 2026-10-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c3e91b2d04'
down_revision: Union[str, Sequence[str], None] = 'd283495802c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

shops = sa.table("shops", sa.column("id", sa.Integer), sa.column("name", sa.String), sa.column("slug", sa.String))


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('shops',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_shops'))
    )
    with op.batch_alter_table('shops', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_shops_slug'), ['slug'], unique=True)

    # Inserted without an explicit id, so Postgres's sequence stays in step for the next shop.
    op.bulk_insert(shops, [{"name": "Default shop", "slug": "default"}])
    default_id = op.get_bind().scalar(sa.select(shops.c.id).where(shops.c.slug == "default"))

    for table in ('users', 'knowledge_base'):
        # Added nullable, filled in, then tightened: existing rows need a value before NOT NULL.
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('shop_id', sa.Integer(), nullable=True))
        op.execute(sa.text(f"UPDATE {table} SET shop_id = :shop_id").bindparams(shop_id=default_id))
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column('shop_id', existing_type=sa.Integer(), nullable=False)
            batch_op.create_index(batch_op.f(f'ix_{table}_shop_id'), ['shop_id'], unique=False)
            batch_op.create_foreign_key(
                batch_op.f(f'fk_{table}_shop_id_shops'), 'shops', ['shop_id'], ['id'], ondelete='CASCADE'
            )


def downgrade() -> None:
    """Downgrade schema."""
    for table in ('knowledge_base', 'users'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(batch_op.f(f'fk_{table}_shop_id_shops'), type_='foreignkey')
            batch_op.drop_index(batch_op.f(f'ix_{table}_shop_id'))
            batch_op.drop_column('shop_id')

    with op.batch_alter_table('shops', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_shops_slug'))
    op.drop_table('shops')
