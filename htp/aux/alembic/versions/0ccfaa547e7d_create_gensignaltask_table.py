"""create genSignalTask table

Revision ID: 0ccfaa547e7d
Revises: 4fb65b7a9050
Create Date: 2019-12-01 17:42:42.477887

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '0ccfaa547e7d'
down_revision = '4fb65b7a9050'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'genSignalTask',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, unique=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('sma_close_x', sa.String(15)),
        sa.Column('sma_close_y', sa.String(15)),
        sa.Column('trade_direction', sa.String(4)),
        sa.Column('exit_strategy', sa.String(20)),
        sa.Column('status', sa.Integer),
        sa.Column('signal_count', sa.Integer),
        sa.Column('batch_number', sa.Integer),
    )


def downgrade():
    op.drop_table('genSignalTask')
