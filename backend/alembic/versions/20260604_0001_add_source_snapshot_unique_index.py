"""add source snapshot unique index

Add a partial unique index on source_snapshots(source_key, content_hash)
WHERE source_key IS NOT NULL so that a registered source never has two
snapshots with identical content.  source_key is nullable (raw/manual
snapshots), so the index is partial.

Revision ID: 20260604_0001
Revises: 20260522_0001
Create Date: 2026-06-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260604_0001"
down_revision = "20260522_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        bind.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS"
                " uq_source_snapshots_source_key_content_hash"
                " ON source_snapshots (source_key, content_hash)"
                " WHERE source_key IS NOT NULL"
            )
        )
    else:
        bind.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS"
                " uq_source_snapshots_source_key_content_hash"
                " ON source_snapshots (source_key, content_hash)"
                " WHERE source_key IS NOT NULL"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DROP INDEX IF EXISTS uq_source_snapshots_source_key_content_hash"
        )
    )
