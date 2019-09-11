import os
from os import DirEntry
import shutil
from pathlib import Path
from functools import partial
from shutil import SameFileError, SpecialFileError
from .utils import cp_stat, cp_dirstat, user_in_group, dircmp


def set_owner_mode_xattr(src, dst, follow_symlinks=False):
    ispath = (isinstance(src, Path) and isinstance(dst, Path))
    isdirentry = (isinstance(src, DirEntry) and isinstance(dst, DirEntry))
    if not (isdirentry and ispath):
        src = Path(src)
        dst = Path(dst)

    if isdirentry:
        src_stat = src.stat(follow_symlinks=follow_symlinks)
        dst_stat = dst.stat(follow_symlinks=follow_symlinks)
    else:
        src_stat = src.stat()
        dst_stat = dst.stat()
        if src.is_symlink():
            src_stat = src_stat if follow_symlinks else src.lstat()
        if dst.is_symlink():
            dst_stat = dst_stat if follow_symlinks else dst.lstat()

    # set mode and extra attributes
    if not (src_stat.st_mode == dst_stat.st_mode):
        # try except not necessary?
        os.chmod(dst, mode=src_stat.st_mode)
        shutil._copyxattr(src, dst, follow_symlinks=follow_symlinks)

    # set time atime, mtime
    src_times = (src_stat.st_atime_ns, src_stat.st_mtime_ns)
    dst_times = (dst_stat.st_atime_ns, dst_stat.st_mtime_ns)

    if not src_times == dst_times:
        os.utime(dst, ns=(src_stat.st_atime_ns, src_stat.st_mtime_ns),
                 follow_symlinks=follow_symlinks)

    # change ownership
    isuser = (src_stat.st_uid == os.getuid())
    isgroup = (src_stat.st_gid == os.getgid())
    # if file is not owned by user running the program
    if not (isuser and isgroup):
        try:
            os.chown(dst, src_stat.st_uid, src_stat.st_gid,
                     follow_symlinks=follow_symlinks)
        except PermissionError:
            raise PermissionError(f"Permissions of {dst} cannot be changed to that of {src}")

def log_or_print(msg, logger=None):
    if logger:
        logger.warn(msg)
    else:
        print(msg)


def handle_exception(ex, fi=None, fi_dst=None, logger=None):
    if type(ex) == SameFileError:
        msg = f"Skipping: {str(fi.path)} and {str(fi_dst)} are same"
        log_or_print(msg, logger=logger)
    elif type(ex) == SpecialFileError:
        msg = f"Skipping: {str(fi.path)} is a special file"
        log_or_print(msg, logger=logger)
    elif type(ex) == PermissionError:
        msg = f"{ex}\nHint:Do you have enough permissions to change file ownership?"
        log_or_print(msg, logger=logger)
    elif type(ex) == OSError:
        msg = f"{ex}\nHint:Possible racing condition?"
        log_or_print(msg, logger=logger)
    elif type(ex) == IOError:
        msg = f"{ex}\nHint:Disk out of space?"
        log_or_print(msg, logger=logger)
    else:
        msg = f"{ex}\n Unknown exception to the program"\
               "raise an issue with developers"
        log_or_print(msg, logger=logger)

def copy(src, dst, ignore=None, logger=None, **kwargs):
    """
    Copies from files and directories from
    `source` to `destination` retaining directory
    structure and file permissions and ownership

    ignore will ignore a directory will not scan the directory
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
        kwargs['scope'] = str(os.path.realpath(src))

    if not dst.exists():
        #os.makedirs(dst)
        os.mkdir(dst)
        # do not raise exceptions here so that root dirs can be scanned recursively
        try:
            set_owner_mode_xattr(src, dst)
        except Exception as ex:
            pass

    # enquiring file stat on DirEntry of scandir is
    # siginicantly faster then using scr.iterdir()
    # or os.walk()
    for fi in os.scandir(src):
        # is destination writable?
        # is contains enough space?
        # filter for files and group
        # ignore only files otherwise scanning dirs owned by root is not possible
        if ignore is not None:
            if fi.is_file() and ignore(fi):
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
                    # handle below better then exists, link could have changed
                    if not fi_dst.exists():
                        os.symlink(newrelpath, fi_dst) 
                    # permissions of source file are retained.
                    set_owner_mode_xattr(fi, fi_dst)
            
                # file outside scope of original src
                else:
                    # maintain the out-of-scope symlink
                    # TODO: new symlink with absolute path?
                    shutil.copy2(fi, fi_dst, follow_symlinks=False)
                    set_owner_mode_xattr(fi, fi_dst)
            elif fi.is_dir():
                # reccursive call to copy
                copy(fi, fi_dst)
                set_owner_mode_xattr(fi, fi_dst)
            # all files
            # if file type is not supported for coping
            # raises error
            elif fi.is_file():
                shutil.copy2(fi, fi_dst, follow_symlinks=False)
                os.utime(fi_dst, 
                         ns=(fi.stat().st_atime_ns, fi.stat().st_mtime_ns),
                         follow_symlinks=False)
                set_owner_mode_xattr(fi, fi_dst)
            else:
                msg = f"Skipping: {str(fi.path)} is special file"
                if logger:
                    logger.warn(msg)
                else:
                    print(msg)

        except SameFileError:
            msg = f"Skipping: {str(fi.path)} and {str(fi_dst)} are same"
            if logger:
                logger.warn(msg)
            else:
                print(msg)
        except SpecialFileError:
            msg = f"Skipping: {str(fi.path)} is a special file"
            print(msg)
        except PermissionError as ex:
            msg = "Do you have enough permissions to change file ownership?"
            if logger:
                logger.error(f"{fi.path} to {fi_dst} {ex} \n{msg}")
            else:
                print(msg, ex)
        except OSError as ex:
            msg = "Possible racing condition?"
            print(ex, msg)
        except IOError as ex:
            if logger:
                logger.critical(ex)
            else:
                print(ex)
    # remove empty not 
    if ignore is not None:
        # check if dir not ignored is empty
        if fi.is_dir() and ignore(fi):
            try:
                dst.rmdir()
            except Exception:
                pass


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


def verify(src, dst):
    src = Path(src)
    dst = Path(dst)
    match, mismatch, miss = dircmp(src, dst)
    compare = {'Match': match,
               'Mismatch': mismatch,
               'Miss': miss}
    return compare


def move(src, dst, ignore, logger):
    """
    dirs are created files are moved and directory is deleted if empty
    """

    src = Path(src)
    dst = Path(dst)
    
    # check if src and dst exist
    # and are directories
    
    # for 

