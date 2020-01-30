"""drop get id column from signals table

Revision ID: 4e9d98be262d
Revises: 936cfe97ee13
Create Date: 2020-01-30 06:25:13.817984

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '4e9d98be262d'
down_revision = '936cfe97ee13'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('signals', 'get_id')


def downgrade():
    op.add_column('signals', sa.Column(
        'get_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id"),
        unique=False))
