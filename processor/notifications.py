import logging
import smtplib
import ssl
from typing import List

from processor import is_email_configured, get_email_config


logger = logging.getLogger(__name__)


def send_email(recipients: List[str], subject: str, message: str) -> bool:
    """
    Send an email to a sysadmin or something.
    :param recipients: email addresses to send to
    :param subject:
    :param message: plaintext message
    :return: boolean success
    """
    if not is_email_configured():
        logger.warning("Ignoring cowardly attempt send email to {} when no email configured".format(recipients))
        return False
    email_config = get_email_config()
    logger.info("Sending email from={} to={}".format(email_config['from_address'], recipients))
    msg = "Subject: {}\n\n{}".format(subject, message)
    context = ssl.create_default_context()
    with smtplib.SMTP(email_config['address'], email_config['port']) as server:
        server.starttls(context=context)
        server.login(email_config['user_name'], email_config['password'])
        for email_address in recipients:
            server.sendmail(email_config['from_address'], email_address, msg.encode("utf8"))
    logger.info("  sent")
    return True
