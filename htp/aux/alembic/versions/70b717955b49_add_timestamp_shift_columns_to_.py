"""add timestamp_shift columns to indicator tables


Revision ID: 70b717955b49
Revises: f3c77ed11415
Create Date: 2020-01-28 16:02:21.142108

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70b717955b49'
down_revision = 'f3c77ed11415'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stochastic', sa.Column('timestamp_shift', sa.DateTime()))
    op.add_column('relativestrengthindex',
                  sa.Column('timestamp_shift', sa.DateTime()))
    op.add_column('ichimokukinkohyo',
                  sa.Column('timestamp_shift', sa.DateTime()))
    op.add_column('movavgconvdiv', sa.Column('timestamp_shift', sa.DateTime()))
    op.add_column('momentum', sa.Column('timestamp_shift', sa.DateTime()))


def downgrade():
    op.drop_column('stochastic', 'timestamp_shift')
    op.drop_column('relativestrengthindex', 'timestamp_shift')
    op.drop_column('momentum', 'timestamp_shift')
    op.drop_column('movavgconvdiv', 'timestamp_shift')
    op.drop_column('ichimokukinkohyo', 'timestamp_shift')
