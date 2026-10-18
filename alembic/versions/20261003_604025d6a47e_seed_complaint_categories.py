"""seed complaint categories

A fixed list an admin picks from when assigning a category — see app.routes.service_requests
.list_categories. Not meant to be edited through the app yet, so it's seeded here rather than
through a script, and exists in every environment the migrations run in, tests included.

Revision ID: 604025d6a47e
Revises: c1774945e289
Create Date: 2026-10-03 13:37:51.716276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '604025d6a47e'
down_revision: Union[str, Sequence[str], None] = 'c1774945e289'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIES = [
    {"category_name": "Electrical", "description": "Wiring, power supply, motors, switchgear.", "urgency_level": "high"},
    {"category_name": "Mechanical", "description": "Moving parts, bearings, belts, structural wear.", "urgency_level": "medium"},
    {"category_name": "HVAC", "description": "Heating, ventilation, air conditioning and refrigeration.", "urgency_level": "medium"},
    {"category_name": "Plumbing", "description": "Pipes, pumps, valves, water and fluid systems.", "urgency_level": "medium"},
    {"category_name": "Electronic", "description": "Control boards, sensors, displays and instrumentation.", "urgency_level": "low"},
    {"category_name": "General", "description": "Anything that doesn't fit a more specific category.", "urgency_level": "low"},
]

complaint_categories = sa.table(
    "complaint_categories",
    sa.column("category_name", sa.String),
    sa.column("description", sa.Text),
    sa.column("urgency_level", sa.String),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(complaint_categories, CATEGORIES)


def downgrade() -> None:
    """Downgrade schema."""
    names = [category["category_name"] for category in CATEGORIES]
    op.execute(complaint_categories.delete().where(complaint_categories.c.category_name.in_(names)))
