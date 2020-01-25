"""create relativestrengthindex table

Revision ID: 3d421fa5601f
Revises: 167ef3c33109
Create Date: 2020-01-25 17:46:28.980836

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '3d421fa5601f'
down_revision = '167ef3c33109'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'relativestrengthindex',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('avg_gain', sa.Float(precision=6)),
        sa.Column('avg_loss', sa.Float(precision=6)),
        sa.Column('rs', sa.Float(precision=6)),
        sa.Column('rsi', sa.Float(precision=6)))


def downgrade():
    op.drop_table('stochastic')
