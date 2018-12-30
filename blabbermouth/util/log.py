import logging
import logging.handlers

_REGISTERED_LOGGERS = []


def logged(cls):
    logger = logging.getLogger(cls.__name__)
    _REGISTERED_LOGGERS.append(logger)
    cls._log = logger
    return cls


def name_to_log_level(name):
    return getattr(logging, name)


def setup_logging(conf):
    logging_conf = conf["logging"]

    log_formatter = logging.Formatter(logging_conf["format"])

    file_handler = logging.handlers.RotatingFileHandler(
        logging_conf["file_handler"]["file_name"],
        mode="a",
        maxBytes=logging_conf["file_handler"]["limit_megabytes"] * 1024 * 1024,
        backupCount=logging_conf["file_handler"]["backup_count"],
        encoding=None,
        delay=logging_conf["file_handler"]["delay"],
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(
        name_to_log_level(logging_conf["file_handler"]["log_level"])
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    stream_handler.setLevel(
        name_to_log_level(logging_conf["stream_handler"]["log_level"])
    )

    for logger in _REGISTERED_LOGGERS:
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
