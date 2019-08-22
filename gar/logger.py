import logging
from logging import handlers
import os
import gzip
from pathlib import Path


__syslogpath = Path("/var/log/gar")

logger = logging.getLogger("gar")

try:
    if __syslogpath.exists() and os.access(__syslogpath, os.W_OK):
        __logfilepath = __syslogpath
    else:
        __logfilepath = Path("~").expanduser() / ".gar"
        __logfilepath.mkdir(exist_ok=True)

except (OSError, PermissionError):
    logger.critical("Logging disabled: gar cannot create logs.\
                     Run gar as adm group\
                     or see if ~/.gar has write permissions")


fh = handlers.TimedRotatingFileHandler((__logfilepath / "gar.log"),
                                       when="s", backupCount=10, delay=True)
formatter = logging.Formatter(' %(asctime)-12s - %(name)-5s \
                              - %(levelname)-6s - %(message)s')
fh.setFormatter(formatter)


def rotator(src, dst):
    os.rename(src, dst)
    with open(dst, 'rb') as f:
        with gzip.open(f'{dst}.gz', mode="wb") as zf:
            zf.writelines(f)
    os.remove(dst)


fh.rotator = rotator

logger.addHandler(fh)
# import time
# time.sleep(10)
# for i in range(1000):
#     time.sleep(0.01)
#     logger.warning("help") # default is warning level
