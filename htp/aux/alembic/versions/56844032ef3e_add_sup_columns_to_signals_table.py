"""add sup columns to signals table

Revision ID: 56844032ef3e
Revises: f2b9e8b3ac73
Create Date: 2020-01-29 10:23:40.953177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56844032ef3e'
down_revision = 'f2b9e8b3ac73'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'signals', sa.Column('sup_percK', sa.Float(precision=6)))
    op.add_column(
        'signals', sa.Column('sup_percD', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('sup_rsi', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('sup_macd', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('sup_histogram',
                                       sa.Float(precision=6)))
    op.add_column('signals', sa.Column('sup_signal', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('sup_adx', sa.Float(precision=6)))
    op.add_column('signals', sa.Column('sup_iky_cat', sa.String(120)))


def downgrade():
    op.drop_column('signals', 'sup_percK')
    op.drop_column('signals', 'sup_percD')
    op.drop_column('signals', 'sup_rsi')
    op.drop_column('signals', 'sup_histogram')
    op.drop_column('signals', 'sup_signal')
    op.drop_column('signals', 'sup_macd')
    op.drop_column('signals', 'sup_iky_cat')
    op.drop_column('signals', 'sup_adx')
