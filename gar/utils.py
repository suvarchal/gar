import os
import grp
import pwd
from pathlib import Path

passwdfi = Path("/etc/passwd")
passwdfi = passwdfi if passwdfi.exists() and os.access(passwdfi,os.R_OK) else None


def getgid(group):
    """Get gid for group
    """
    if type(group) is str:
        gid = grp.getgrnam(group).gr_gid
        return gid
    elif type(group) is int:
        gid = grp.getgrgid(group).gr_gid
        return gid
