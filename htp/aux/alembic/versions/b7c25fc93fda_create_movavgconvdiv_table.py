"""create movavgconvdiv table

Revision ID: b7c25fc93fda
Revises: e54b35b1e615
Create Date: 2020-01-25 17:01:52.510870

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'b7c25fc93fda'
down_revision = 'e54b35b1e615'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'movavgconvdiv',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('emaS', sa.Float(precision=6)),
        sa.Column('emaF', sa.Float(precision=6)),
        sa.Column('macd', sa.Float(precision=6)),
        sa.Column('signal', sa.Float(precision=6)),
        sa.Column('histogram', sa.Float(precision=6)))


def downgrade():
    op.drop_table('movavgconvdiv')
