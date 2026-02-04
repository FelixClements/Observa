# -*- coding: utf-8 -*-

#  This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.

from io import open
import os
import shlex

from apscheduler.triggers.cron import CronTrigger
import email.utils
from sqlalchemy import select, update

import plexpy
from plexpy.services import newsletters
from plexpy.db.models import Newsletter, NewsletterLog
from plexpy.db.session import session_scope
from plexpy.util import helpers
from plexpy.util import logger


NEWSLETTER_SCHED = None


def add_newsletter_each(newsletter_id=None, notify_action=None, **kwargs):
    if not notify_action:
        logger.debug("Tautulli NewsletterHandler :: Notify called but no action received.")
        return

    data = {'newsletter': True,
            'newsletter_id': newsletter_id,
            'notify_action': notify_action}
    data.update(kwargs)
    plexpy.NOTIFY_QUEUE.put(data)


def schedule_newsletters(newsletter_id=None):
    newsletters_list = newsletters.get_newsletters(newsletter_id=newsletter_id)

    for newsletter in newsletters_list:
        newsletter_job_name = '{} (newsletter_id {})'.format(newsletter['agent_label'], newsletter['id'])

        if newsletter['active']:
            schedule_newsletter_job('newsletter-{}'.format(newsletter['id']), name=newsletter_job_name,
                                    func=add_newsletter_each, args=[newsletter['id'], 'on_cron'], cron=newsletter['cron'])
        else:
            schedule_newsletter_job('newsletter-{}'.format(newsletter['id']), name=newsletter_job_name,
                                    remove_job=True)


def schedule_newsletter_job(newsletter_job_id, name='', func=None, remove_job=False, args=None, cron=None):
    if cron:
        values = shlex.split(cron)
        # apscheduler day_of_week uses 0-6 = mon-sun
        values[4] = str((int(values[4]) - 1) % 7) if values[4].isdigit() else values[4]

    if NEWSLETTER_SCHED.get_job(newsletter_job_id):
        if remove_job:
            NEWSLETTER_SCHED.remove_job(newsletter_job_id)
            logger.info("Tautulli NewsletterHandler :: Removed scheduled newsletter: %s" % name)
        else:
            try:
                NEWSLETTER_SCHED.reschedule_job(
                    newsletter_job_id, args=args, trigger=CronTrigger(
                        minute=values[0], hour=values[1], day=values[2], month=values[3], day_of_week=values[4]
                    )
                )
                logger.info("Tautulli NewsletterHandler :: Re-scheduled newsletter: %s" % name)
            except ValueError as e:
                logger.error("Tautulli NewsletterHandler :: Failed to re-schedule newsletter: %s" % e)
    elif not remove_job:
        try:
            NEWSLETTER_SCHED.add_job(
                func, args=args, id=newsletter_job_id, trigger=CronTrigger(
                    minute=values[0], hour=values[1], day=values[2], month=values[3], day_of_week=values[4]
                ),
                misfire_grace_time=None
            )
            logger.info("Tautulli NewsletterHandler :: Scheduled newsletter: %s" % name)
        except ValueError as e:
            logger.error("Tautulli NewsletterHandler :: Failed to schedule newsletter: %s" % e)


def notify(newsletter_id=None, notify_action=None, **kwargs):
    logger.info("Tautulli NewsletterHandler :: Preparing newsletter for newsletter_id %s." % newsletter_id)

    newsletter_config = newsletters.get_newsletter_config(newsletter_id=newsletter_id)

    if not newsletter_config:
        return

    if notify_action in ('test', 'api'):
        subject = kwargs.pop('subject', None) or newsletter_config['subject']
        body = kwargs.pop('body', None) or newsletter_config['body']
        message = kwargs.pop('message', None) or newsletter_config['message']
    else:
        subject = newsletter_config['subject']
        body = newsletter_config['body']
        message = newsletter_config['message']

    email_msg_id = email.utils.make_msgid()
    email_reply_msg_id = get_last_newsletter_email_msg_id(newsletter_id=newsletter_id, notify_action=notify_action)

    newsletter_agent = newsletters.get_agent_class(newsletter_id=newsletter_id,
                                                   newsletter_id_name=newsletter_config['id_name'],
                                                   agent_id=newsletter_config['agent_id'],
                                                   config=newsletter_config['config'],
                                                   email_config=newsletter_config['email_config'],
                                                   subject=subject,
                                                   body=body,
                                                   message=message,
                                                   email_msg_id=email_msg_id,
                                                   email_reply_msg_id=email_reply_msg_id
                                                   )

    # Set the newsletter state in the db
    newsletter_log_id = set_notify_state(newsletter=newsletter_config,
                                         notify_action=notify_action,
                                         subject=newsletter_agent.subject_formatted,
                                         body=newsletter_agent.body_formatted,
                                         message=newsletter_agent.message_formatted,
                                         filename=newsletter_agent.filename_formatted,
                                         start_date=newsletter_agent.start_date.format('YYYY-MM-DD'),
                                         end_date=newsletter_agent.end_date.format('YYYY-MM-DD'),
                                         start_time=newsletter_agent.start_time,
                                         end_time=newsletter_agent.end_time,
                                         newsletter_uuid=newsletter_agent.uuid,
                                         email_msg_id=email_msg_id)

    # Send the notification
    success = newsletter_agent.send()

    if success:
        set_notify_success(newsletter_log_id)
        return True


def set_notify_state(newsletter, notify_action, subject, body, message, filename,
                     start_date, end_date, start_time, end_time, newsletter_uuid, email_msg_id):

    if newsletter and notify_action:
        try:
            with session_scope() as session:
                log_entry = session.execute(
                    select(NewsletterLog).where(NewsletterLog.uuid == newsletter_uuid)
                ).scalar_one_or_none()
                if log_entry is None:
                    log_entry = NewsletterLog(uuid=newsletter_uuid)
                    session.add(log_entry)

                log_entry.timestamp = helpers.timestamp()
                log_entry.newsletter_id = newsletter['id']
                log_entry.agent_id = newsletter['agent_id']
                log_entry.agent_name = newsletter['agent_name']
                log_entry.notify_action = notify_action
                log_entry.subject_text = subject
                log_entry.body_text = body
                log_entry.message_text = message
                log_entry.start_date = start_date
                log_entry.end_date = end_date
                log_entry.start_time = start_time
                log_entry.end_time = end_time
                log_entry.email_msg_id = email_msg_id
                log_entry.filename = filename
                session.flush()
                return log_entry.id
        except Exception as e:
            logger.warn("Tautulli NewsletterHandler :: Failed to set notify state: %s" % e)
            return None
    else:
        logger.error("Tautulli NewsletterHandler :: Unable to set notify state.")


def set_notify_success(newsletter_log_id):
    with session_scope() as session:
        session.execute(
            update(NewsletterLog)
            .where(NewsletterLog.id == newsletter_log_id)
            .values(success=1)
        )


def get_last_newsletter_email_msg_id(newsletter_id, notify_action):
    stmt = (
        select(NewsletterLog.email_msg_id)
        .where(
            NewsletterLog.newsletter_id == newsletter_id,
            NewsletterLog.notify_action == notify_action,
            NewsletterLog.success == 1,
        )
        .order_by(NewsletterLog.timestamp.desc())
        .limit(1)
    )

    with session_scope() as session:
        return session.execute(stmt).scalar_one_or_none()


def get_newsletter(newsletter_uuid=None, newsletter_id_name=None):
    if newsletter_uuid:
        stmt = (
            select(
                NewsletterLog.start_date,
                NewsletterLog.end_date,
                NewsletterLog.uuid,
                NewsletterLog.filename,
            )
            .where(NewsletterLog.uuid == newsletter_uuid)
        )
    elif newsletter_id_name:
        stmt = (
            select(
                NewsletterLog.start_date,
                NewsletterLog.end_date,
                NewsletterLog.uuid,
                NewsletterLog.filename,
            )
            .join(Newsletter, Newsletter.id == NewsletterLog.newsletter_id)
            .where(
                Newsletter.id_name == newsletter_id_name,
                NewsletterLog.notify_action != 'test',
            )
            .order_by(NewsletterLog.timestamp.desc())
            .limit(1)
        )
    else:
        result = None

    if newsletter_uuid or newsletter_id_name:
        with session_scope() as session:
            result = session.execute(stmt).mappings().first()

    if result:
        newsletter_uuid = result['uuid']
        start_date = result['start_date']
        end_date = result['end_date']
        newsletter_file = result['filename'] or 'newsletter_%s-%s_%s.html' % (start_date.replace('-', ''),
                                                                              end_date.replace('-', ''),
                                                                              newsletter_uuid)

        newsletter_folder = plexpy.CONFIG.NEWSLETTER_DIR or os.path.join(plexpy.DATA_DIR, 'newsletters')
        newsletter_file_fp = os.path.join(newsletter_folder, newsletter_file)

        if newsletter_file in os.listdir(newsletter_folder):
            try:
                with open(newsletter_file_fp, 'r', encoding='utf-8') as n_file:
                    newsletter = n_file.read()
                return newsletter
            except OSError as e:
                logger.error("Tautulli NewsletterHandler :: Failed to retrieve newsletter '%s': %s" % (newsletter_uuid, e))
        else:
            logger.warn("Tautulli NewsletterHandler :: Newsletter file '%s' is missing." % newsletter_file)
