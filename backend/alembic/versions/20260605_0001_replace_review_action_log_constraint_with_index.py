"""replace review action log constraint with unique index

Replace the unique constraint on review_action_logs
(review_item_id, actor, action) with a unique index.
This migration is safe to re-run because it uses IF NOT
EXISTS / IF EXISTS guards and catches failures when the
constraint is absent.

Revision ID: 20260605_0001
Revises: 20260604_0002
Create Date: 2026-06-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260605_0001"
down_revision = "20260604_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Drop the constraint if it exists (from original 0002 form).
    # Gracefully ignore failure when the constraint is absent.
    try:
        op.drop_constraint(
            "uq_review_action_log_item_actor_action",
            "review_action_logs",
            type_="unique",
        )
    except Exception:
        pass

    # Create the unique index if it does not already exist.
    bind.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "uq_review_action_log_item_actor_action "
            "ON review_action_logs (review_item_id, actor, action)"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    # After upgrade there is only a standalone unique index (no constraint).
    # Drop it before recreating the original unique constraint.
    bind.execute(
        sa.text(
            "DROP INDEX IF EXISTS uq_review_action_log_item_actor_action"
        )
    )

    # Recreate the original unique constraint.
    op.create_unique_constraint(
        "uq_review_action_log_item_actor_action",
        "review_action_logs",
        ["review_item_id", "actor", "action"],
    )
