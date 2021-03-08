import os
import logging
import sys
from dotenv import load_dotenv
import mediacloud.api
from flask import Flask
from sentry_sdk import init, capture_message
from typing import Dict

VERSION = "1.0.0"

load_dotenv()  # load config from .env file (local) or env vars (production)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.info("------------------------------------------------------------------------")
logger.info("Starting up Feminicide MC Story Processor v{}".format(VERSION))

# read in environment variables
MC_API_KEY = os.environ.get('MC_API_KEY', None)  # sensitive, so don't log it
if MC_API_KEY is None:
    logger.error("  No MC_API_KEY env var specified. Pathetically refusing to start!")
    sys.exit(1)

BROKER_URL = os.environ.get('BROKER_URL', None)
if BROKER_URL is None:
    logger.error("No BROKER_URL env var specified. Pathetically refusing to start!")
    sys.exit(1)
logger.info("  Redis at {}".format(BROKER_URL))

SENTRY_DSN = os.environ.get('SENTRY_DSN', None)  # optional
if SENTRY_DSN:
    init(dsn=SENTRY_DSN)
    capture_message("Initializing")
    logger.info("  SENTRY_DSN: {}".format(SENTRY_DSN))
else:
    logger.info("  Not logging errors to Sentry")

CONFIG_FILE_URL = os.environ.get('CONFIG_FILE_URL', None)
if CONFIG_FILE_URL is None:
    logger.error("  No CONFIG_FILE_URL is specified. Bailing because we can't list projects to run!")
    sys.exit(1)
else:
    logger.info("  Project list at {}".format(CONFIG_FILE_URL))

FEMINICIDE_API_KEY = os.environ.get('FEMINICIDE_API_KEY', None)
if FEMINICIDE_API_KEY is None:
    logger.error("  No FEMINICIDE_API_KEY is specified. Bailing because we can't send things to the main server without one")
    sys.exit(1)


def get_mc_client() -> mediacloud.api.AdminMediaCloud:
    """
    A central place to get the Media Cloud client
    :return: an admin media cloud client with the API key from the environment variable
    """
    return mediacloud.api.AdminMediaCloud(MC_API_KEY)


def create_flask_app() -> Flask:
    """
    Create and configure the Flask app. Standard practice is to do this in a factory method like this.
    :return: a fully configured Flask web app
    """
    return Flask(__name__)


def is_email_configured() -> bool:
    return (os.environ.get('SMTP_USER_NAME', None) is not None) and \
            (os.environ.get('SMTP_PASSWORD', None) is not None) and \
            (os.environ.get('SMTP_ADDRESS', None) is not None) and \
            (os.environ.get('SMTP_PORT', None) is not None) and \
            (os.environ.get('SMTP_FROM', None) is not None) and \
            (os.environ.get('NOTIFY_EMAILS', None) is not None)


def get_email_config() -> Dict:
    return dict(
        user_name=os.environ.get('SMTP_USER_NAME', None),
        password=os.environ.get('SMTP_PASSWORD', None),
        address=os.environ.get('SMTP_ADDRESS', None),
        port=os.environ.get('SMTP_PORT', None),
        from_address=os.environ.get('SMTP_FROM', None),
        notify_emails=os.environ.get('NOTIFY_EMAILS', "").split(",")
    )
