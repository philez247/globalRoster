"""add_user_role_to_trader

Revision ID: 6dcd3eb9a3f7
Revises: 5ba7ee707e1c
Create Date: 2025-12-08 17:26:46.104075

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dcd3eb9a3f7'
down_revision = '5ba7ee707e1c'
branch_labels = None
depends_on = None

# Define the enum type
user_role_enum = sa.Enum("USER", "OWNER", "MANAGER", "ADMIN", name="user_role_enum")


def upgrade() -> None:
    # Create enum type (SQLite will store as string, but we define it for consistency)
    # For SQLite, we'll use String with a check constraint
    # For PostgreSQL/other DBs, this would create a proper enum type
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # SQLite doesn't support native enums, so we use String
        op.add_column(
            'traders',
            sa.Column(
                'user_role',
                sa.String(20),
                nullable=False,
                server_default='USER',
            ),
        )
        # Backfill existing rows with 'USER'
        op.execute("UPDATE traders SET user_role = 'USER' WHERE user_role IS NULL OR user_role = ''")
    else:
        # For other databases, create the enum type
        user_role_enum.create(bind, checkfirst=True)
        op.add_column(
            'traders',
            sa.Column(
                'user_role',
                user_role_enum,
                nullable=False,
                server_default='USER',
            ),
        )


def downgrade() -> None:
    op.drop_column('traders', 'user_role')
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        user_role_enum.drop(bind, checkfirst=True)



