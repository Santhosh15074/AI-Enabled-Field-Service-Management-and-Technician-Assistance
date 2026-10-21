"""config portal: operators, and per-shop settings

Operators are Sollu's own staff, who set up and configure shops in the config portal. Shops get
the settings that portal edits: active or not, plan, technician and report limits, and a contact
phone. Existing shops (just "default" so far) start active, on Starter.

Revision ID: b8d4f02c3e15
Revises: a7c3e91b2d04
Create Date: 2026-10-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d4f02c3e15'
down_revision: Union[str, Sequence[str], None] = 'a7c3e91b2d04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('operators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=60), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_operators'))
    )
    with op.batch_alter_table('operators', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_operators_email'), ['email'], unique=True)

    # Server defaults only so the existing rows get a value; the app always sets these itself.
    with op.batch_alter_table('shops', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))
        batch_op.add_column(sa.Column('plan', sa.String(length=20), server_default='starter', nullable=False))
        batch_op.add_column(sa.Column('technician_limit', sa.Integer(), server_default='10', nullable=False))
        batch_op.add_column(sa.Column('monthly_report_limit', sa.Integer(), server_default='750', nullable=False))
        batch_op.add_column(sa.Column('contact_phone', sa.String(length=20), nullable=True))
        batch_op.create_check_constraint(
            op.f('ck_shops_plan_valid'), "plan IN ('starter', 'growth', 'pro')"
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('shops', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_shops_plan_valid'), type_='check')
        batch_op.drop_column('contact_phone')
        batch_op.drop_column('monthly_report_limit')
        batch_op.drop_column('technician_limit')
        batch_op.drop_column('plan')
        batch_op.drop_column('is_active')

    with op.batch_alter_table('operators', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_operators_email'))
    op.drop_table('operators')
