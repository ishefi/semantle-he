import logging


def setup_logger() -> logging.Logger:
    log = logging.getLogger("web app")
    log.setLevel(logging.DEBUG)
    return log


logger = setup_logger()
