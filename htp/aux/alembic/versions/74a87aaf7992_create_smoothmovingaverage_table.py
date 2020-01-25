"""create smoothmovingaverage table

Revision ID: 74a87aaf7992
Revises: 16411ed1210c
Create Date: 2020-01-25 12:41:22.762466

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '74a87aaf7992'
down_revision = '16411ed1210c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'smoothmovingaverage',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('close_sma_3', sa.Float(precision=6)),
        sa.Column('close_sma_4', sa.Float(precision=6)),
        sa.Column('close_sma_5', sa.Float(precision=6)),
        sa.Column('close_sma_6', sa.Float(precision=6)),
        sa.Column('close_sma_7', sa.Float(precision=6)),
        sa.Column('close_sma_8', sa.Float(precision=6)),
        sa.Column('close_sma_9', sa.Float(precision=6)),
        sa.Column('close_sma_10', sa.Float(precision=6)),
        sa.Column('close_sma_12', sa.Float(precision=6)),
        sa.Column('close_sma_14', sa.Float(precision=6)),
        sa.Column('close_sma_15', sa.Float(precision=6)),
        sa.Column('close_sma_16', sa.Float(precision=6)),
        sa.Column('close_sma_20', sa.Float(precision=6)),
        sa.Column('close_sma_24', sa.Float(precision=6)),
        sa.Column('close_sma_25', sa.Float(precision=6)),
        sa.Column('close_sma_28', sa.Float(precision=6)),
        sa.Column('close_sma_30', sa.Float(precision=6)),
        sa.Column('close_sma_32', sa.Float(precision=6)),
        sa.Column('close_sma_35', sa.Float(precision=6)),
        sa.Column('close_sma_36', sa.Float(precision=6)),
        sa.Column('close_sma_40', sa.Float(precision=6)),
        sa.Column('close_sma_48', sa.Float(precision=6)),
        sa.Column('close_sma_50', sa.Float(precision=6)),
        sa.Column('close_sma_60', sa.Float(precision=6)),
        sa.Column('close_sma_64', sa.Float(precision=6)),
        sa.Column('close_sma_70', sa.Float(precision=6)),
        sa.Column('close_sma_72', sa.Float(precision=6)),
        sa.Column('close_sma_80', sa.Float(precision=6)),
        sa.Column('close_sma_90', sa.Float(precision=6)),
        sa.Column('close_sma_96', sa.Float(precision=6)),
        sa.Column('close_sma_100', sa.Float(precision=6)))


def downgrade():
    op.drop_table('smoothmovingaverage')
