"""
Revision ID: 202602060001
Revises: 202602040001
Create Date: 2026-02-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '202602060001'
down_revision = '202602040001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sessions s "
            "USING sessions s2 "
            "WHERE s.session_key IS NOT NULL "
            "AND s2.session_key IS NOT NULL "
            "AND s.session_key = s2.session_key "
            "AND s.id < s2.id"
        )
    )

    op.create_unique_constraint('idx_sessions_session_key', 'sessions', ['session_key'])


def downgrade() -> None:
    op.drop_constraint('idx_sessions_session_key', 'sessions', type_='unique')
