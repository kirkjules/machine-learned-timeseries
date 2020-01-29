"""add close to ... columns to signals table

Revision ID: cf5059379cad
Revises: 56844032ef3e
Create Date: 2020-01-29 11:06:00.944044

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf5059379cad'
down_revision = '56844032ef3e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('signals', sa.Column('close_in_atr', sa.Integer))
    op.add_column('signals', sa.Column('close_to_fast_by_atr',
                                       sa.Float(precision=6)))
    op.add_column('signals', sa.Column('close_to_slow_by_atr',
                                       sa.Float(precision=6)))


def downgrade():
    op.drop_column('signals', 'close_in_atr')
    op.drop_column('signals', 'close_to_fast_by_atr')
    op.drop_column('signals', 'close_to_slow_by_atr')
