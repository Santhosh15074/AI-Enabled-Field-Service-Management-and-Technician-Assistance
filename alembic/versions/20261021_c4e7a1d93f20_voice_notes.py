"""voice notes

A technician's recorded account of a job, and its transcript — see app.models.VoiceNote.

Revision ID: c4e7a1d93f20
Revises: b8d4f02c3e15
Create Date: 2026-10-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e7a1d93f20'
down_revision: Union[str, Sequence[str], None] = 'b8d4f02c3e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('voice_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('recorded_by', sa.Integer(), nullable=True),
    sa.Column('client_id', sa.String(length=64), nullable=False),
    sa.Column('audio_path', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=100), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('transcript', sa.Text(), nullable=True),
    sa.Column('engine', sa.String(length=150), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('transcribed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('pending', 'transcribing', 'done', 'failed')", name=op.f('ck_voice_notes_status_valid')),
    sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], name=op.f('fk_voice_notes_recorded_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['request_id'], ['service_requests.id'], name=op.f('fk_voice_notes_request_id_service_requests'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_voice_notes')),
    sa.UniqueConstraint('client_id', name=op.f('uq_voice_notes_client_id'))
    )
    with op.batch_alter_table('voice_notes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_voice_notes_request_id'), ['request_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('voice_notes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_voice_notes_request_id'))
    op.drop_table('voice_notes')
