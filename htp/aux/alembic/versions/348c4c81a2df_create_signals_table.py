"""create signals table

Revision ID: 348c4c81a2df
Revises: 3d421fa5601f
Create Date: 2020-01-27 11:28:30.706277

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '348c4c81a2df'
down_revision = '3d421fa5601f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'signals',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("genSignalTask.id"),
            unique=False),
        sa.Column(
            'get_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id"),
            unique=False),
        sa.Column('entry_datetime', sa.DateTime()),
        sa.Column('entry_price', sa.Float(precision=6)),
        sa.Column('stop_loss', sa.Float(precision=6)),
        sa.Column('exit_datetime', sa.DateTime()),
        sa.Column('exit_price', sa.Float(precision=6)))


def downgrade():
    op.drop_table('signals')
