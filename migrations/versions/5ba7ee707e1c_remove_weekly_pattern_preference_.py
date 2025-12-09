"""remove_weekly_pattern_preference_overrides

Revision ID: 5ba7ee707e1c
Revises: 3577bf871923
Create Date: 2025-12-08 16:10:44.163559

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ba7ee707e1c'
down_revision = '3577bf871923'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop override tables
    op.drop_index(op.f('ix_trader_weekly_pattern_overrides_week_start'), table_name='trader_weekly_pattern_overrides')
    op.drop_index(op.f('ix_trader_weekly_pattern_overrides_trader_id'), table_name='trader_weekly_pattern_overrides')
    op.drop_index(op.f('ix_trader_weekly_pattern_overrides_id'), table_name='trader_weekly_pattern_overrides')
    op.drop_table('trader_weekly_pattern_overrides')
    op.drop_index(op.f('ix_trader_preference_overrides_week_start'), table_name='trader_preference_overrides')
    op.drop_index(op.f('ix_trader_preference_overrides_trader_id'), table_name='trader_preference_overrides')
    op.drop_index(op.f('ix_trader_preference_overrides_id'), table_name='trader_preference_overrides')
    op.drop_table('trader_preference_overrides')


def downgrade() -> None:
    # Recreate override tables (reverse of 3577bf871923)
    op.create_table('trader_preference_overrides',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trader_id', sa.Integer(), nullable=False),
    sa.Column('week_start', sa.Date(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('key', sa.String(length=50), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['trader_id'], ['traders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('trader_id', 'week_start', 'category', 'key', name='uq_trader_preference_override')
    )
    op.create_index(op.f('ix_trader_preference_overrides_id'), 'trader_preference_overrides', ['id'], unique=False)
    op.create_index(op.f('ix_trader_preference_overrides_trader_id'), 'trader_preference_overrides', ['trader_id'], unique=False)
    op.create_index(op.f('ix_trader_preference_overrides_week_start'), 'trader_preference_overrides', ['week_start'], unique=False)
    op.create_table('trader_weekly_pattern_overrides',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trader_id', sa.Integer(), nullable=False),
    sa.Column('week_start', sa.Date(), nullable=False),
    sa.Column('day_of_week', sa.Integer(), nullable=False),
    sa.Column('shift_type', sa.String(length=10), nullable=False),
    sa.Column('hard_block', sa.Boolean(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['trader_id'], ['traders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('trader_id', 'week_start', 'day_of_week', 'shift_type', name='uq_trader_weekly_pattern_override')
    )
    op.create_index(op.f('ix_trader_weekly_pattern_overrides_id'), 'trader_weekly_pattern_overrides', ['id'], unique=False)
    op.create_index(op.f('ix_trader_weekly_pattern_overrides_trader_id'), 'trader_weekly_pattern_overrides', ['trader_id'], unique=False)
    op.create_index(op.f('ix_trader_weekly_pattern_overrides_week_start'), 'trader_weekly_pattern_overrides', ['week_start'], unique=False)

