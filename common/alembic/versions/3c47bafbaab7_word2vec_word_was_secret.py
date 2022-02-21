"""word2vec - word was secret

Revision ID: 3c47bafbaab7
Revises: 9e67a0a418e4
Create Date: 2022-02-21 20:52:46.179727

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c47bafbaab7'
down_revision = '9e67a0a418e4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'word2vec',
        sa.Column("secret_date", sa.Date),
    )


def downgrade():
    op.drop_column('word2vec', "was_secret")
