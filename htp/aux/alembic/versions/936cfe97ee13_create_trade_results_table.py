"""create trade_results table

Revision ID: 936cfe97ee13
Revises: cf5059379cad
Create Date: 2020-01-29 17:16:19.060526

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '936cfe97ee13'
down_revision = 'cf5059379cad'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'trade_results',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("genSignalTask.id"),
            unique=False),
        sa.Column('exit_datetime', sa.DateTime()),
        sa.Column('PL_PIPS', sa.Float(precision=2)),
        sa.Column('POS_SIZE', sa.Integer),
        sa.Column('PL_AUD', sa.Float(precision=2)),
        sa.Column('PL_REALISED', sa.Float(precision=2)))


def downgrade():
    op.drop_table('trade_results')
