import logging

def get_logger(name: str, level=logging.DEBUG):
    """
    Returns a configured logger.
    
    name: module name (e.g., 'server.network', 'client.main')
    log_file: optional path to a file. If None, defaults to <LOG_DIR>/<name>.log
    level: logging level
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if logger is already configured
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
