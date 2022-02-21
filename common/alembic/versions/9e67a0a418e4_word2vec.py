"""word2vec

Revision ID: 9e67a0a418e4
Revises: 
Create Date: 2022-02-18 20:01:06.057791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e67a0a418e4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "word2vec",
        sa.Column("word", sa.Text, primary_key=True, nullable=False),
        sa.Column("vec", sa.LargeBinary, nullable=False),
    )


def downgrade():
    op.drop_table('word2ved')
