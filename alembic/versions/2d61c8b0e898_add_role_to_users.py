"""add role to users

Revision ID: 2d61c8b0e898
Revises: be796bc979cd
Create Date: 2026-07-16 12:32:53.000032

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.enums.roles import UserRole

# revision identifiers, used by Alembic.
revision: str = "2d61c8b0e898"
down_revision: Union[str, Sequence[str], None] = "be796bc979cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                    CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member');
                END IF;
            END
            $$;
            """)

    op.add_column(
        "users",
        sa.Column(
            "role",
            postgresql.ENUM(
                UserRole.OWNER.value,
                UserRole.ADMIN.value,
                UserRole.MEMBER.value,
                name="user_role",
                create_type=False,
            ),
            nullable=False,
            server_default=UserRole.MEMBER.value,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS user_role")
