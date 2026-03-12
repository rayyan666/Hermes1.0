import logging
import os

os.makedirs('logs', exist_ok=True)


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))
        logger.addHandler(handler)
    return logger


def log_startup(msg):
    log = get_logger('startup')
    log.info(msg)
