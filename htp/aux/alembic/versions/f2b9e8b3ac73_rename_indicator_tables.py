"""rename indicator tables

Revision ID: f2b9e8b3ac73
Revises: af38b8a34e00
Create Date: 2020-01-29 06:59:38.777605

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2b9e8b3ac73'
down_revision = 'af38b8a34e00'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('ichimokukinkohyo', 'ichimoku')
    op.rename_table('smoothmovingaverage', 'moving_average')
    op.rename_table('relativestrengthindex', 'relative_strength')
    op.rename_table('movavgconvdiv', 'convergence_divergence')


def downgrade():
    op.rename_table('ichimoku', 'ichimokukinkohyo')
    op.rename_table('moving_average', 'smoothmovingaverage')
    op.rename_table('relative_strength', 'relativestrengthindex')
    op.rename_table('convergence_divergence', 'movavgconvdiv') 
