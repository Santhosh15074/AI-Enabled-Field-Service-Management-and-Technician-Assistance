"""request triage

How each request's urgency was decided and why, and whether its category was picked by AI — see
app.ml.triage. Nullable: requests from before this had their urgency from the classifier alone.

Revision ID: e6a9c3f15b42
Revises: d5f8b2e04a31
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6a9c3f15b42'
down_revision: Union[str, Sequence[str], None] = 'd5f8b2e04a31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('service_requests') as batch_op:
        batch_op.add_column(sa.Column('urgency_source', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('urgency_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('category_source', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('service_requests') as batch_op:
        batch_op.drop_column('category_source')
        batch_op.drop_column('urgency_reason')
        batch_op.drop_column('urgency_source')
