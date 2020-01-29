"""add property columns to signals table

Revision ID: fc48f4d33e48
Revises: 70b717955b49
Create Date: 2020-01-28 18:22:32.283295

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc48f4d33e48'
down_revision = '70b717955b49'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'signals', sa.Column('target_percK', sa.Float(precision=6)))
    op.add_column(
        'signals', sa.Column('target_percD', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('target_rsi', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('target_macd', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('target_histogram',
                                       sa.Float(precision=6)))
    op.add_column('signals', sa.Column('target_signal', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('target_adx', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('target_iky_cat', sa.String(120)))


def downgrade():
    op.drop_column('signals', 'target_percK')
    op.drop_column('signals', 'target_percD')
    op.drop_column('signals', 'target_rsi')
    op.drop_column('signals', 'target_histogram')
    op.drop_column('signals', 'target_signal')
    op.drop_column('signals', 'target_macd')
    op.drop_column('signals', 'target_iky_cat')
    op.drop_column('signals', 'target_adx')
