"""add from and to columns to getTickerTask table

Revision ID: 27047c3aa544
Revises: 0ccfaa547e7d
Create Date: 2020-01-12 08:25:27.417084

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27047c3aa544'
down_revision = '0ccfaa547e7d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('getTickerTask', sa.Column('_from', sa.DateTime()))
    op.add_column('getTickerTask', sa.Column('to', sa.DateTime()))


def downgrade():
    op.drop_column('getTickerTask', '_from')
    op.drop_column('getTickerTask', 'to')
