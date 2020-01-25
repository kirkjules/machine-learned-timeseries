"""create stochastic table

Revision ID: 167ef3c33109
Revises: 95016193f1ff
Create Date: 2020-01-25 17:33:58.164875

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '167ef3c33109'
down_revision = '95016193f1ff'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stochastic',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('percK', sa.Float(precision=6)),
        sa.Column('percD', sa.Float(precision=6)))


def downgrade():
    op.drop_table('stochastic')
