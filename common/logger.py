import logging


def setup_logger():
    log = logging.getLogger("web app")
    log.setLevel(logging.DEBUG)
    return log


logger = setup_logger()
