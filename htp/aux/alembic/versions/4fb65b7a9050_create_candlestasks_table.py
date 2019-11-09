"""create CandlesTasks table

Revision ID: 4fb65b7a9050
Revises:
Create Date: 2019-11-09 09:17:26.919310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fb65b7a9050'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'candlestasks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('ticker', sa.String(50)),
        sa.Column('from_', sa.DateTime()),
        sa.Column('to', sa.DateTime()),
        sa.Column('granularity', sa.String(3)),
        sa.Column('price', sa.String(1)),
        sa.Column('task_id', sa.String(50)),
        sa.Column('task_status', sa.String(50)),
        sa.Column('task_error', sa.String(120))
    )


def downgrade():
    op.drop_table('candlestasks')
