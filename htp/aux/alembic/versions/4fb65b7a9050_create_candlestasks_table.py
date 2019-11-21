"""create CandlesTasks table

Revision ID: 4fb65b7a9050
Revises:
Create Date: 2019-11-09 09:17:26.919310

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '4fb65b7a9050'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'getTickerTask',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, unique=True),
        sa.Column('ticker', sa.String(50)),
        sa.Column('granularity', sa.String(3)),
        sa.Column('price', sa.String(1)),
        sa.Column('status', sa.Integer)
    )
    op.create_table(
        'subTickerTask',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, unique=True),
        sa.Column(
            'get_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('_from', sa.DateTime(), nullable=False),
        sa.Column('to', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Integer),
        sa.Column('error', sa.String(120))
    )
    op.create_table(
        'indicatorTask',
        sa.Column(
            'get_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id"),
            primary_key=True, unique=True),
        sa.Column('adx_status', sa.Integer),
        sa.Column('atr_status', sa.Integer),
        sa.Column('stochastic_status', sa.Integer),
        sa.Column('rsi_status', sa.Integer),
        sa.Column('macd_status', sa.Integer),
        sa.Column('ichimoku_status', sa.Integer),
        sa.Column('sma_status', sa.Integer),
        sa.Column('status', sa.Integer)
    )


def downgrade():
    op.drop_table('subTickerTask')
    op.drop_table('indicatorTask')
    op.drop_table('getTickerTask')
