"""Secret word table

Revision ID: 734535a7c997
Revises: 23e3fa471b40
Create Date: 2024-01-14 18:09:54.747781

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "734535a7c997"
down_revision: Union[str, None] = "23e3fa471b40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "secretword",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            "word", sa.String(32, collation="Hebrew_100_CI_AI_SC_UTF8"), nullable=False
        ),
        sa.Column("game_date", sa.Date(), nullable=False),
        sa.Column("solver_count", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_date"),
        sa.UniqueConstraint("word"),
    )


def downgrade() -> None:
    op.drop_table("secretword")
