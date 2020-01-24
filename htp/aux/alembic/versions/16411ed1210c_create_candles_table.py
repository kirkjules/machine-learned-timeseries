"""create Candles table

Revision ID: 16411ed1210c
Revises: 27047c3aa544
Create Date: 2020-01-24 18:07:40.159835

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '16411ed1210c'
down_revision = '27047c3aa544'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'candles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('open', sa.Float(precision=6)),
        sa.Column('high', sa.Float(precision=6)),
        sa.Column('low', sa.Float(precision=6)),
        sa.Column('close', sa.Float(precision=6)))


def downgrade():
    op.drop_table('candles')
