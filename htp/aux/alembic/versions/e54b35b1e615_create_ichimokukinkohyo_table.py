"""create ichimokukinkohyo table

Revision ID: e54b35b1e615
Revises: 74a87aaf7992
Create Date: 2020-01-25 13:12:09.697102

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e54b35b1e615'
down_revision = '74a87aaf7992'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ichimokukinkohyo',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('tenkan', sa.Float(precision=6)),
        sa.Column('kijun', sa.Float(precision=6)),
        sa.Column('chikou', sa.Float(precision=6)),
        sa.Column('senkou_A', sa.Float(precision=6)),
        sa.Column('senkou_B', sa.Float(precision=6)))


def downgrade():
    op.drop_table('ichimokukinkohyo')
