import os
import shutil
from pathlib import Path
from functools import partial
from shutil import SameFileError, SpecialFileError
from .utils import cp_stat, cp_dirstat, user_in_group


def set_owner_mode_xattr(src, dst):
    # src = Path(src)
    # dst = Path(dst)
    src_stat = src.stat()
    #os.chown(dst, src_stat.st_uid, src_stat.st_gid)
    os.chmod(dst, mode=src_stat.st_mode)
    #os.utime(dst, times=(src_stat.st_atime, src_stat.st_mtime))
    #shutil._copyxattr(src, dst)


def lset_owner_mode_xattr(src, dst):
    # src = Path(src)
    # dst = Path(dst)
    src_stat = src.stat()
    #os.chown(dst, src_stat.st_uid, src_stat.st_gid, follow_symlinks=False)
    os.chmod(dst, mode=src_stat.st_mode)
    #os.utime(dst, ns=(src_stat.st_atime_ns, src_stat.st_mtime_ns), follow_symlinks=False)
    #shutil._copyxattr(src, dst, follow_symlinks=False)


def copy(src, dst, ignore=None, logger=None, **kwargs):
    """
    Copies from files and directories from
    `source` to `destination` retaining directory
    structure and file permissions and ownership

    Returns None
    """
    if logger:
        logger.__setattr__("name", "copy")

    src = Path(src)
    dst = Path(dst)
    
    # disable the function for src that is not a directory
    if src.is_file():
        raise NotADirectoryError(f"src {src} is a file, pass a directory")

    # a trick to send original src information to
    # recursive call of the function
    if 'scope' not in kwargs:
        kwargs['scope'] = str(src)

    if not dst.exists():
        #os.makedirs(dst)
        os.mkdir(dst)
        # try block?
        set_owner_mode_xattr(src, dst)
        print(src,src.stat().st_atime_ns, src.stat().st_mtime_ns)
        print(dst,dst.stat().st_atime_ns, dst.stat().st_mtime_ns)
        os.utime(dst, ns=(src.stat().st_atime_ns, src.stat().st_mtime_ns), follow_symlinks=False)
        print(dst,dst.stat().st_atime_ns, dst.stat().st_mtime_ns)
        print(cp_stat(dst))
        print(cp_dirstat(dst))

    # enquiring file stat on DirEntry of scandir is
    # siginicantly faster then using scr.iterdir()
    # or os.walk()
    for fi in os.scandir(src):
        # is destination writable?
        # is contains enough space?
        # filter for files and group
        if ignore is not None:
            if ignore(fi):
                continue

        fi_dst = dst / fi.name
        try:
            if fi.is_symlink():
                # to check if the link in scope of original src
                commonpath = os.path.commonpath([os.path.realpath(fi),
                                                 src.absolute()])
                # check if target of link is within original src
                # if so dont copy, just link
                if commonpath == kwargs['scope']:
                    newrelpath = os.path.relpath(os.path.realpath(fi), src)
                    os.symlink(newrelpath, fi_dst)
                    # permissions of source file are retained.
                    #lset_owner_mode_xattr(fi, fi_dst)
                    os.utime(fi_dst, ns=(fi.stat().st_atime_ns, fi.stat().st_mtime_ns), follow_symlinks=False)
            
                # file outside scope of original src
                else:
                    # maintain the out-of-scope symlink
                    shutil.copy2(fi, fi_dst, follow_symlinks=False)
                    #lset_owner_mode_xattr(fi, fi_dst)
                    os.utime(fi_dst, ns=(fi.stat().st_atime_ns, fi.stat().st_mtime_ns), follow_symlinks=False)
            elif fi.is_dir():
                # reccursive call to copy
                copy(fi, fi_dst)
                os.utime(fi_dst, ns=(fi.stat().st_atime_ns, fi.stat().st_mtime_ns), follow_symlinks=False)
                #set_owner_mode_xattr(fi, fi_dst)
            # all files
            # if file type is not supported for coping
            # raises error
            else:
                shutil.copy2(fi, fi_dst, follow_symlinks=False)
                os.utime(fi_dst, ns=(fi.stat().st_atime_ns, fi.stat().st_mtime_ns), follow_symlinks=False)
                #set_owner_mode_xattr(fi, fi_dst)

        except (SameFileError, SpecialFileError) as ex:
            msg = f"Skipping {ex.filename} same as {ex.filename1}"
            if logger:
                logger.warn(msg)
            else:
                print(msg)
        except (OSError, PermissionError) as ex:
            msg = "Do you have enough permissions to change file ownership?\n"\
                  "Run as privilaged user or see `gar --help` for options."
            if logger:
                logger.error(f"{fi.path} to {fi_dst} {ex} \n{msg}")
            else:
                print(msg,ex.filename,ex.filename2, ex)
        except IOError as ex:
            if logger:
                logger.critical(ex)
            else:
                print(ex)


def ignore_not_group(group, srcfile, ignorefilegroup=True):
    """ srcfile must be a pathlib.Path object
        default checks based on owner of file in group
        checkfilegroup chgrp
        returns True to ignore and False if not
    """
    src_stat = srcfile.stat()
    uig = user_in_group(src_stat.st_uid, group)

    if ignorefilegroup:
        return not uig
    else:
        gid = getgid(group)
        return not (src_stat.st_gid == gid or uig)


def gcopy(group, src, dst):
    """TODO:handle skip from cli"""
    ignore_fn = partial(ignore_not_group, group) # ignorefilegroup=False)
    copy(src, dst, ignore=ignore_fn)
