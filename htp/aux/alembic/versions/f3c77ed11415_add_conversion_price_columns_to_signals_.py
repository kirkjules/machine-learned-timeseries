"""add conversion price columns to signals table

Revision ID: f3c77ed11415
Revises: e7e27074ea48
Create Date: 2020-01-28 06:58:50.596960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3c77ed11415'
down_revision = 'e7e27074ea48'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'signals', sa.Column('conv_entry_price', sa.Float(precision=6)))
    op.add_column(
        'signals', sa.Column('conv_exit_price', sa.Float(precision=6)))


def downgrade():
    op.drop_column('signals', 'conv_entry_price')
    op.drop_column('signals', 'conv_exit_price')
