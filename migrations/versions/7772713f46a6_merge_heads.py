"""Merge heads

Revision ID: 7772713f46a6
Revises: 428f318c07c3, add_isfavorite_column
Create Date: 2025-05-26 10:25:11.755985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7772713f46a6'
down_revision = ('428f318c07c3', 'add_isfavorite_column')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
