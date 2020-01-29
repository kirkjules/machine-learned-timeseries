"""add iky_cat column to ichimoku table

Revision ID: af38b8a34e00
Revises: fc48f4d33e48
Create Date: 2020-01-28 18:32:53.229785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af38b8a34e00'
down_revision = 'fc48f4d33e48'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ichimokukinkohyo', sa.Column('iky_cat', sa.String(120)))


def downgrade():
    op.drop_column('ichimokukinkohyo', 'iky_cat')
