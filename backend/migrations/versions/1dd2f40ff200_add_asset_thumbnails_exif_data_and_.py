"""Add FK constraint fix for posts.recurring_rule_id (ondelete SET NULL).

Revision ID: 1dd2f40ff200
Revises: a1b2c3d4e5f6
Create Date: 2026-02-16 22:48:32.886380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dd2f40ff200'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix FK constraint on posts.recurring_rule_id to include ON DELETE SET NULL."""
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_posts_recurring_rule_id', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_posts_recurring_rule_id',
            'recurring_post_rules',
            ['recurring_rule_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    """Revert FK constraint to original (no ON DELETE clause)."""
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_posts_recurring_rule_id', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_posts_recurring_rule_id',
            'recurring_post_rules',
            ['recurring_rule_id'],
            ['id'],
        )
