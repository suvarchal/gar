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
        gm.extend(grp.getgrgid(gid).gr_mem)
    else:
        gm = grp.getgrgid(gid).gr_mem
    return gm

def cp_dirstat(dirpath):
    """ will not reccurse just dir info 
        name, owner, group, mode, modified and access(?)
        are reliable way to check ownership and permissions
    """
    dirpath = Path(dirpath)
    fstat = dirpath.stat()
    if dirpath.is_dir() and not dirpath.is_symlink():

        finfo = {'Name': dirpath.name,
                 'Owner': pwd.getpwuid(fstat.st_uid).pw_name, 
                 'Group': grp.getgrgid(fstat.st_gid).gr_name,
                 'Mode': oct(fstat.st_mode),
                 'Modified': fstat.st_mtime_ns}
                 #'Accessed': fstat.st_atime_ns}
        return OrderedDict(finfo)


def cp_linkstat(fdpath, include_name=True, only_ownership=True,
                follow_symlinks=False):
    """return stat on link that can be compared on copy 
       mode is not used as links are always 777
       size not used as it depends on path link points to
       so comparing doesn't make sense
       ownership option only compares ownership 
    """
    if fdpath.is_symlink():
        if isinstance(fdpath, os.DirEntry):
            fstat = fdpath.stat(follow_symlinks=follow_symlinks)
        else:
            fdpath = Path(fdpath)
            fstat = fdpath.lstat() if not follow_symlinks else fdpath.stat()
    
        finfo = {'Owner': pwd.getpwuid(fstat.st_uid).pw_name,
                 'Group': grp.getgrgid(fstat.st_gid).gr_name}
        
        if not only_ownership:
            finfo.update({'Modified': fstat.st_mtime_ns,
                          'Accessed': fstat.st_atime_ns})
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
             'Modified': time.ctime(fstat.st_mtime),
             'Accessed': time.ctime(fstat.st_atime),
             'Changed': time.ctime(fstat.st_ctime)}
    return OrderedDict(finfo)

def hash_walk(fdpath, follow_symlinks=False, ignore=None):
    """ Returns hash for entire directory tree using default hash.
        function only scans for files, directories and symlinks:
        special files are ignored by the has function
    """
    if not isinstance(fdpath, Path):
        fdpath = Path(fdpath)
    if not fdpath.exists():
        return None
    files_hash = sha1()
    # use walk and sorted to ensure the listing order is same every run
    # files without read permissions will be ignored
    for root, dirs, files in os.walk(fdpath):
        root = Path(root)
        # functions called ignore all other kinds of files (eg.., device files)
        # ignore read errors
        for fi in sorted(files):
            # skip files that are not readable
            if not os.access(fi, os.R_OK):
                continue
            fip = root / fi
            files_hash.update(hash_cp_stat(fip, hash_function=sha1).hexdigest().encode())
        for d in sorted(dirs):
            # remove directory that are not readable from traversing further
            if not os.access(d, os.R_OK):
                dirs.remove(d)
                continue
            dp = root / d
            files_hash.update(hash_cp_stat(dp, hash_function=sha1).hexdigest().encode())
    return files_hash.hexdigest()

def dircmp(src, dst, ignore=None):
    """ Compares files in src to dst for integrity
    returns list of match, missmatch, skip and misses
    use of os.walk makes it skip files and directories
    not readable.
    """
    if not (isinstance(src, Path) and isinstance(dst, Path)):
        src = Path(src)
        dst = Path(dst)
    if not (src.is_dir() and dst.is_dir()):
        raise NotADirectoryError(f"src: {src} and dst: {dst} must be directories")
    match = []
    mismatch = []
    miss = []
    skip = []
    for sroot, sdirs, sfiles in os.walk(src, followlinks=False):
        sroot = Path(sroot)
        for fi in sfiles:
            fisp = sroot / fi
            # ignore files if ignore is True
            if ignore and ignore(fi):
                continue
            fidp = os.path.relpath(os.path.abspath(fisp), src)
            fidp = dst / fidp
            # skips any unsupported file and
            # read errors (eg.., permissions, linkerrors)
            if not os.access(fi, os.R_OK):
                skip.append(fi)
                continue
            if not fidp.exists():
                miss.append((str(fisp), str(fidp)))
                continue
            if cp_stat(fisp) == cp_stat(fidp):
                match.append((str(fisp), str(fidp)))
            else:
                mismatch.append(('file', str(fisp), str(fidp)))
        for di in sdirs:
            dsp = sroot / di
            ddp = os.path.relpath(os.path.abspath(dsp), src)
            ddp = dst / ddp
            # not necessary to check os.R_OK of symlink dir 
            # because dir links are not resolved by os.walk
            if not ddp.exists():
                miss.append((str(dsp), str(ddp)))
                continue
            if cp_stat(dsp) == cp_stat(ddp):
                match.append((str(dsp), str(ddp)))
            else:
                mismatch.append(('dir', str(dsp), str(ddp)))
    return (match, mismatch, miss, skip)



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