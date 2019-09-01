from contextlib import contextmanager
import os
from pathlib import Path
import fcntl


lockpath = Path("/var/lock")

if lockpath.exists() and os.access(lockpath, os.W_OK):
    lockpath = lockpath
else:
    lockpath = Path.home()

class SimpleFileLock:
    def __init__(self, lockfile):
        self.lockfile = lockpath / lockfile

    def __enter__(self):
        if os.path.exists(self.lockfile):
            raise OSError("Cannot acquire lock: Another process running")
        try:
            os.open(self.lockfile, os.O_CREAT, 0o640)
        except OSError as e:
            raise SystemExit(e)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.lockfile)

class FileLock:
    """ doesn't work perfectly yet
    """
    def __init__(self, lockfile):
        self.lockfile = lockpath / lockfile
    def __enter__(self):
        try:
            lock_fd = os.open(self.lockfile, os.O_CREAT, 0o640)
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError,OSError) as e:
            os.close(lock_fd)
            raise OSError(e) #SystemExit(e)
    def __exit__(self, exc_type, exc_val, exc_tb):
        #os.close(lock_fd)
        os.remove(self.lockfile)
