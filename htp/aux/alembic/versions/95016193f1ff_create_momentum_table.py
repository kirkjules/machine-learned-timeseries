"""create momentum table

Revision ID: 95016193f1ff
Revises: b7c25fc93fda
Create Date: 2020-01-25 17:16:59.395995

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '95016193f1ff'
down_revision = 'b7c25fc93fda'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'momentum',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'batch_id', UUID(as_uuid=True), sa.ForeignKey("getTickerTask.id")),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('atr', sa.Float(precision=6)),
        sa.Column('adx', sa.Float(precision=6)))


def downgrade():
    op.drop_table('momentum')
