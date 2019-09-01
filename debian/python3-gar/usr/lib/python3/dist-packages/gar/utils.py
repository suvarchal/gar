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


def group_members(group):
    """Replacement for grp.gr_mem
       grp module doesnt report group members
       from memebers with group as primary members
    """
    gid = grp.getgrnam(group).gr_gid

    if passwdfi:
        with open(passwdfi) as f:
            users = f.readlines()
        gm = []
        for u in users:
            ul = u.split(":")
            if ul[3] == str(gid):
                gm.append(ul[0])
    else:
        gm = grp.getgrgid(group).gr_mem
    return gm
