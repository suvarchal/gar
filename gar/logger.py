import logging
from logging import handlers
import os
import gzip
from pathlib import Path


syslogpath = Path("/var/log/gar")

logger = logging.getLogger("logging")

try:
    if syslogpath.exists() and os.access(syslogpath, os.W_OK):
        logfilepath = syslogpath
    else:
        logfilepath = Path.home() / ".gar"
        logfilepath.mkdir(exist_ok=True)

except (OSError, PermissionError):
    logger.critical("Logging disabled: gar cannot create logs.\
                     Run gar as adm group\
                     or see if ~/.gar has write permissions")


def rotator(src, dst):
    os.rename(src, dst)
    with open(dst, 'rb') as f:
        with gzip.open(f"{dst}.gz", mode="wb") as zf:
            zf.writelines(f)
    os.remove(dst)


def setup_logger(name="gar.log"):
    fh = handlers.TimedRotatingFileHandler((logfilepath / name),
                                           when="s", backupCount=10,
                                           delay=True)
    # use formatter with just message for now
    # formatter = logging.Formatter(' %(asctime)-12s - %(name)-5s \
    #                              - %(levelname)-6s - %(message)s')
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)

    fh.rotator = rotator

    logger.addHandler(fh)
    return fh
