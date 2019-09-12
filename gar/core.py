import os
from os import DirEntry
import shutil
from pathlib import Path
from functools import partial
from shutil import SameFileError, SpecialFileError
from .utils import cp_stat, cp_dirstat, user_in_group, dircmp, getgid


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
    if isinstance(ex, SameFileError):
        msg = f"Skipping: {str(fi.path)} and {str(fi_dst)} are same"
        log_or_print(msg, logger=logger)
    elif isinstance(ex, SpecialFileError):
        msg = f"Skipping: {str(fi.path)} is unsupported file"
        log_or_print(msg, logger=logger)
    elif isinstance(ex, PermissionError):
        msg = f"{ex}\n"\
               "Hint: Do you have enough permissions to change file ownership?"
        log_or_print(msg, logger=logger)
    elif isinstance(ex, OSError):
        msg = f"{ex}"
        log_or_print(msg, logger=logger)
    elif isinstance(ex, IOError):
        msg = f"{ex}\nHint: Disk out of space?"
        log_or_print(msg, logger=logger)
    else :
        msg = f"{ex}\n Unknown exception {str(type(ex))} to the program, "\
               "please raise an issue with developers"
        log_or_print(msg, logger=logger)

def copy(src, dst, ignore=None, logger=None, **kwargs):
    """
    Copies from files and directories from
    `source` to `destination` retaining directory
    structure and file permissions and ownership
    
    scandir is used for efficiency reasons

    ignore will ignore a directory will not scan the directory
    Returns None
    """
    if logger:
        logger.__setattr__("name", "copy")
    
    # trick to a identify reccursive call or not
    # else src will be dir entry
    if 'scope' not in kwargs:
        src = Path(src)
        kwargs['scope'] = str(os.path.realpath(src))
    
    # discard scanning directories and files that are not readable 
    if not os.access(src, os.R_OK):
        raise OSError(f"Skipping: {src.path} cannot be read")
    
    dst = Path(dst)
    
    # disable the function for src that is not a directory
    if src.is_file():
        raise NotADirectoryError(f"src {src} is a file, pass a directory")

    if not dst.exists():
        os.mkdir(dst)

    # enquiring file stat on DirEntry of scandir is
    # siginicantly faster then using scr.iterdir()
    # or os.walk()
    for fi in os.scandir(src):
        # is contains enough space?
        # filter for files
        # ignore only files otherwise scanning dirs owned
        # by root is not possible
        if ignore:
            if fi.is_file() and ignore(fi):
                continue

        fi_dst = dst / fi.name
        try:
            if fi.is_symlink():
                # to check if the link in scope of original src
                # use os.readlink(fi) instead?
                commonpath = os.path.commonpath([os.path.realpath(fi),
                                                 kwargs['scope']])
                # check if target of link is within original src
                # if so dont copy, just link
                if commonpath == kwargs['scope']:
                    newrelpath = os.path.relpath(os.path.realpath(fi), src)
                    # handle below better for recopy, link could have changed
                    if not fi_dst.exists():
                        os.symlink(newrelpath, fi_dst) 
                    # permissions of source link are retained.
                    set_owner_mode_xattr(fi, fi_dst)
            
                # file outside scope of original src
                else:
                    # maintain the out-of-scope symlink
                    # TODO: new symlink with absolute path?
                    shutil.copy(fi, fi_dst, follow_symlinks=False)
                    set_owner_mode_xattr(fi, fi_dst)
            elif fi.is_dir():
                # reccursive call to copy
                copy(fi, fi_dst, ignore=ignore, logger=logger, **kwargs)
                set_owner_mode_xattr(fi, fi_dst)
            # all files
            # if file type is not supported for coping
            # raises error
            elif fi.is_file():
                shutil.copy(fi, fi_dst, follow_symlinks=False)
                set_owner_mode_xattr(fi, fi_dst)
            else:
                msg = f"Skipping: {str(fi.path)} is a unsupported file"
                log_or_print(msg, logger=logger)

            if ignore:
                # check if dir not ignored is empty is so remove
                if fi.is_dir() and ignore(fi):
                    try:
                        fi_dst.rmdir()
                    except OSError:
                        pass
        except Exception as ex:
            handle_exception(ex, fi, fi_dst, logger)
        # remove empty directories that are ignored
    try:
        if not os.path.realpath(src) == kwargs['scope']:
            set_owner_mode_xattr(src, dst)
    except Exception as ex:
        handle_exception(ex, src, dst)
    return dst


def ignore_not_group(group, srcfile, ignorefilegroup=True):
    """ srcfile must be a pathlib.Path object
        default checks based on owner of file in group
        checkfilegroup chgrp
        returns True to ignore and False if not
    """
    if isinstance(srcfile, DirEntry):
        src_stat = srcfile.stat(follow_symlinks=False)
    else:
        srcfile = Path(srcfile)
        src_stat = srcfile.lstat() if srcfile.is_symlink() else srcfile.stat()

    uig = user_in_group(src_stat.st_uid, group)
    # return false owner in group
    if ignorefilegroup:
        return not uig
    else:
        gid = getgid(group)
        return not (src_stat.st_gid == gid or uig)


def gcopy(group, src, dst):
    """TODO:handle skip from cli"""
    ignore_fn = partial(ignore_not_group, group)
    copy(src, dst, ignore=ignore_fn)


def verify(src, dst):
    """ gverify?
    """
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

