"""ai suggestions

The saved AI troubleshooting draft for a request that matched nothing in the knowledge base — see
app.models.AiSuggestion and app.ml.ai_fallback.

Revision ID: d5f8b2e04a31
Revises: c4e7a1d93f20
Create Date: 2026-10-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f8b2e04a31'
down_revision: Union[str, Sequence[str], None] = 'c4e7a1d93f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ai_suggestions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('model', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['request_id'], ['service_requests.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('request_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ai_suggestions')
