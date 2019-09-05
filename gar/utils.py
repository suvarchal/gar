import os
import grp
import pwd
import time
import json
import time
from pathlib import Path
from collections import OrderedDict
from hashlib import sha1

passwdfi = Path("/etc/passwd")
passwdfi = passwdfi if passwdfi.exists() and os.access(passwdfi, os.R_OK) else None


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
        gm = grp.getgrgid(gid).gr_mem
    return gm

def cp_dirstat(dirpath):
    """ will not reccurse just dir info
    """
    dirpath = Path(dirpath)
    fstat = dirpath.stat()
    if dirpath.is_dir() and not dirpath.is_symlink():

        finfo = {'Name': dirpath.name,
                 'Owner': pwd.getpwuid(fstat.st_uid).pw_name, 
                 'Group': grp.getgrgid(fstat.st_gid).gr_name,
                 'Mode': oct(fstat.st_mode),
                 'Modified': fstat.st_mtime_ns,
                 'Accessed': fstat.st_atime_ns}
        return OrderedDict(finfo)


def cp_linkstat(fdpath, include_name=True, follow_symlinks=False):
    """ size not used as it depends on path so comparing doesn't make
        sense
    """
    if fdpath.is_symlink():
        if isinstance(fdpath, os.DirEntry):
            fstat = fdpath.stat(follow_symlinks=follow_symlinks)
        else:
            fdpath = Path(fdpath)
            fstat = fdpath.lstat() if not follow_symlinks else fdpath.stat()
    
        finfo = {'Owner': pwd.getpwuid(fstat.st_uid).pw_name, 
                 'Group': grp.getgrgid(fstat.st_gid).gr_name,
                 'Mode': oct(fstat.st_mode),
                 'Modified': fstat.st_mtime_ns,
                 'Accessed': fstat.st_atime_ns}
        if include_name:
            finfo.update({'Name': fdpath.name})
        return OrderedDict(finfo)


def cp_filestat(filepath):

    if isinstance(filepath, os.DirEntry):
        fstat = filepath.stat()
    else:
        filepath = Path(filepath)
        fstat = filepath.stat()

    if filepath.is_file() and not filepath.is_symlink():
        finfo = {'Name': filepath.name,
                 'Owner': fstat.st_uid, 
                 'Group': fstat.st_gid,
                 'Mode': oct(fstat.st_mode),
                 'Size': fstat.st_size,
                 'Modified': fstat.st_mtime_ns,
                 'Accessed': fstat.st_atime_ns}
        return OrderedDict(finfo)

def cp_stat(fdpath, follow_symlinks=False):
    if type(fdpath) == str:
        fdpath = Path(fdpath)
    if fdpath.is_symlink():
        return cp_linkstat(fdpath, follow_symlinks=follow_symlinks)
    if fdpath.is_file():
        return cp_filestat(fdpath)
    if fdpath.is_dir():
        return cp_dirstat(fdpath)

def hash_cp_stat(fdpath, follow_symlinks=False, hash_function=hash): 
    """ Returns hash of file stat that can be used for shallow comparision
    default python hash function is used which returns a integer. This
    can be used to quickly compare files, for comparing directories
    see hash_walk().
    """
    stat = cp_stat(fdpath, follow_symlinks)
    if stat:
        return hash_function(json.dumps(stat, sort_keys=True).encode("utf-8"))


def hr_filestat(filepath):
    filepath = Path(filepath)
    fstat = filepath.stat()
    finfo = {'Owner': pwd.getpwuid(fstat.st_uid).pw_name, 
             'Group': grp.getgrgid(fstat.st_gid).gr_name,
             'Mode': oct(fstat.st_mode),
             'Size': hr_size(fstat.st_size),
             'Device': fstat.st_dev,
             'Created': time.ctime(fstat.st_ctime),
             'Modified': time.ctime(fstat.st_mtime),
             'Accessed': time.ctime(fstat.st_atime)}
    return OrderedDict(finfo)

def hash_walk(fdpath, follow_symlinks=False, ignore=None):
    """ Returns hash for entire directory tree using default hash.
        function only scans for files, directories and symlinks:
        special files are ignored by the has function
        
    """
    files_hash = sha1()
    # use walk and sorted to ensure the listing order is same every run
    # files without read permissions will be ignored
    for root, dirs, files in os.walk(fdpath):
        root = Path(root)
        # functions called ignore all other kinds of files (eg.., device files)
        # add ignored clause? 
        for fi in sorted(files):
            fip = root / fi
            files_hash.update(hash_cp_stat(fip, hash_function=sha1).hexdigest().encode())
        for d in sorted(dirs):
            dp = root / d
            files_hash.update(hash_cp_stat(dp, hash_function=sha1).hexdigest().encode())
    return files_hash.hexdigest()

def user_in_group(user, group):
    """ Check if user is in group
        user and group can be names(str) or ids(int)
    """
    # handles if user is uid
    if type(user) == int:
        user = pwd.getpwuid(user).pw_name

    # handles if group is id
    if type(group) == int:
        group = grp.getgrgid(group).gr_name

    return user in group_members(group)


def hr_size(size):
    """Returns human readable size
       input size in bytes
    """
    units = ["B","kB","MB","GB","TB","PB"]
    i = 0 # index
    while (size > 1024 and i < len(units)):
        i += 1
        size /= 1024.0
    return f"{size:.2f} {units[i]}"