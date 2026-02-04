"""Add foreign key constraints for history/log tables.

Revision ID: 202602040001
Revises: 202602030001
Create Date: 2026-02-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '202602040001'
down_revision = '202602030001'
branch_labels = None
depends_on = None


def _assert_no_orphans(connection, query: str, label: str) -> None:
    count = connection.execute(sa.text(query)).scalar()
    if count and count > 0:
        raise RuntimeError(
            "Cannot add foreign key %s; found %s orphaned rows." % (label, count)
        )


def upgrade() -> None:
    connection = op.get_bind()

    _assert_no_orphans(
        connection,
        "SELECT COUNT(*) FROM session_history_metadata shm "
        "LEFT JOIN session_history sh ON sh.id = shm.id "
        "WHERE sh.id IS NULL",
        'session_history_metadata.id -> session_history.id',
    )
    _assert_no_orphans(
        connection,
        "SELECT COUNT(*) FROM session_history_media_info shmi "
        "LEFT JOIN session_history sh ON sh.id = shmi.id "
        "WHERE sh.id IS NULL",
        'session_history_media_info.id -> session_history.id',
    )
    _assert_no_orphans(
        connection,
        "SELECT COUNT(*) FROM session_history sh "
        "LEFT JOIN users u ON u.user_id = sh.user_id "
        "WHERE sh.user_id IS NOT NULL AND u.user_id IS NULL",
        'session_history.user_id -> users.user_id',
    )
    _assert_no_orphans(
        connection,
        "SELECT COUNT(*) FROM notify_log nl "
        "LEFT JOIN notifiers n ON n.id = nl.notifier_id "
        "WHERE nl.notifier_id IS NOT NULL AND n.id IS NULL",
        'notify_log.notifier_id -> notifiers.id',
    )
    _assert_no_orphans(
        connection,
        "SELECT COUNT(*) FROM newsletter_log nwl "
        "LEFT JOIN newsletters n ON n.id = nwl.newsletter_id "
        "WHERE nwl.newsletter_id IS NOT NULL AND n.id IS NULL",
        'newsletter_log.newsletter_id -> newsletters.id',
    )

    op.create_foreign_key(
        'fk_session_history_user_id_users',
        'session_history',
        'users',
        ['user_id'],
        ['user_id'],
    )
    op.create_foreign_key(
        'fk_session_history_metadata_id_session_history',
        'session_history_metadata',
        'session_history',
        ['id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_session_history_media_info_id_session_history',
        'session_history_media_info',
        'session_history',
        ['id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_notify_log_notifier_id_notifiers',
        'notify_log',
        'notifiers',
        ['notifier_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_newsletter_log_newsletter_id_newsletters',
        'newsletter_log',
        'newsletters',
        ['newsletter_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_newsletter_log_newsletter_id_newsletters', 'newsletter_log', type_='foreignkey')
    op.drop_constraint('fk_notify_log_notifier_id_notifiers', 'notify_log', type_='foreignkey')
    op.drop_constraint('fk_session_history_media_info_id_session_history', 'session_history_media_info', type_='foreignkey')
    op.drop_constraint('fk_session_history_metadata_id_session_history', 'session_history_metadata', type_='foreignkey')
    op.drop_constraint('fk_session_history_user_id_users', 'session_history', type_='foreignkey')
