"""hot clue table

Revision ID: 8798f64b5f19
Revises: 8240e5d61928
Create Date: 2024-01-17 21:31:45.610168

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8798f64b5f19"
down_revision: Union[str, None] = "8240e5d61928"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hotclue",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("secret_word_id", sa.Integer(), nullable=False),
        sa.Column("clue", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["secret_word_id"],
            ["secretword.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("secret_word_id", "clue"),
    )


def downgrade() -> None:
    op.drop_table("hotclue")
