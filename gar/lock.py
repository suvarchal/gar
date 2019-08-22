from contextlib import contextmanager
import os
from pathlib import Path
import fcntl
__lockpath__ = "/var/lock"

# check if path exists else put it in tmp?
# test if able to lock?

class SimpleFileLock:
    def __init__(self,lockfile):
        self.lockfile = lockfile
    def __enter__(self):
        if os.path.exists(self.lockfile):
            raise OSError("Another gar process running for same group")
        try:
            os.open(self.lockfile, os.O_CREAT, 0o640)
        except OSError as e:
            SystemExit(e)
        
    def __exit__(self, exc_type, exc_val, exc_tb): 
        os.remove(self.lockfile)

class FileLock:
    def __init__(self, lockfile):
        self.lockfile = lockfile
    def __enter__(self):
        os.open(file_n,os.O_CREAT,0o600)
        try:
            fcntl.flock(lock_fd,fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except IOError:
             print("failed")
    def __exit__(self, exc_type, exc_val, exc_tb):

        try:
           os.close(lock_fd)
           os.unlink(file_n)
           print("successfully released lock")
        except:
           print("failed to release lock, clean manually") 
