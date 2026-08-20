"""add query_result_json to agent_runs

Revision ID: a1b2c3d4e5f6
Revises: fd4aa34c9a60
Create Date: 2026-08-20 16:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "fd4aa34c9a60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration."""
    op.add_column(
        "agent_runs",
        sa.Column("query_result_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Revert this migration."""
    op.drop_column("agent_runs", "query_result_json")
