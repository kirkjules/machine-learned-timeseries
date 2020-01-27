"""update column names in genSignalTask

Revision ID: e7e27074ea48
Revises: 348c4c81a2df
Create Date: 2020-01-27 11:56:27.798755

"""
from alembic import op
# import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7e27074ea48'
down_revision = '348c4c81a2df'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('genSignalTask', 'sma_close_x', new_column_name='fast')
    op.alter_column('genSignalTask', 'sma_close_y', new_column_name='slow')


def downgrade():
    op.alter_column('genSignalTask', 'fast', new_column_name='sma_close_x')
    op.alter_column('genSignalTask', 'slow', new_column_name='sma_close_y')
