import os
from os import DirEntry
import shutil
from pathlib import Path
from functools import partial
from shutil import SameFileError, SpecialFileError
from .utils import cp_stat, cp_dirstat, user_in_group, dircmp, getgid


def set_owner_mode_xattr(src, dst, follow_symlinks=False):

    if isinstance(src, DirEntry):
        src_stat = src.stat(follow_symlinks=follow_symlinks)
    else:
        src = Path(src)
        if src.is_symlink():
            src_stat = src.stat() if (follow_symlinks and src.exists()) else src.lstat()
        else:
            src_stat = src.stat()

    if isinstance(dst, DirEntry):
        dst_stat = dst.stat(follow_symlinks=follow_symlinks)
    else:
        dst = Path(dst)
        # this can raise file not found for .stat() when target to symlink
        # doesn't exist handle this by adding option ignore dangling links
        if dst.is_symlink():
            dst_stat = dst.stat() if (follow_symlinks and dst.exists()) else dst.lstat()
        else:
            dst_stat = dst.stat()
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
        except PermissionError as ex:
            raise PermissionError(f"Mismatch: {ex.filename} "
                                  "ownership cannot be assigned.")


def log_or_print(msg, logger=None):
    """ print or log 
    only one is allowed if both is required ass stdout
    handler to logger
    """
    if logger:
        logger.warn(msg)
    else:
        print(msg)


def handle_exception(ex, fi=None, fi_dst=None, logger=None):
    """Handle exceptions mostly by type except IOError
    TODO: group skipping exceptions into a new skipping
    exception type
    """
    if type(ex) == SameFileError:
        msg = f"Skipping: {str(fi.path)} and {str(fi_dst)} are same."
        log_or_print(msg, logger=logger)
    elif type(ex) == SpecialFileError:
        msg = f"Skipping: {str(fi.path)} is a unsupported file."
        log_or_print(msg, logger=logger)
    elif type(ex) == PermissionError:
        msg = f"{ex}\n"\
               "\tHint: Do you have enough permissions "\
               "to change file ownership?"
        log_or_print(msg, logger=logger)
    elif type(ex) == FileNotFoundError:
        msg = f"Skipping: {ex}\n"\
               "\t Hint: Possible racing condition?"
    elif type(ex) == OSError:
        msg = f"{ex}"
        log_or_print(ex, logger=logger)
    # handle any instance of IOError
    elif isinstance(ex, IOError):
        msg = f"{ex}\n\tHint: Disk out of space?"
        log_or_print(msg, logger=logger)
    # raise error if other exceptions occur
    else:
        msg = f"{ex}\n Unknown exception {ex.args[0]} to the program, "\
               "please raise an issue with developers."
        log_or_print(msg)


def copy(src, dst, ignore=None, logger=None, **kwargs):
    """
    Copies from files and directories from
    `source` to `destination` retaining directory
    structure and file permissions, access and modification times
    and ownership. ownership is maintained only if possible bys
    the user (eg.., root). if not possible file is owned by user running
    the process.

    symlinks are retained to target of src if the target is out of scope
    and creates a new symlink to new target in dst if symlink is in scope
    of src.This is a feature unlike shell linux standard cp or python
    standard library shutil.copytree would do.

    ignore can be used to ignore certain files (only files not directories)
    ignore can be a callable that takes filename as input and returns boolean
    to ignore(True) or not(False)

    logger allows logging to a remote logger.

    directories are scanned using scandir for efficiency reasons.

    Returns dst
    """
    if logger:
        logger.__setattr__("name", "copy")

    # To a identify not in reccursive call/ first call to function
    # else src will be direntry
    if 'scope' not in kwargs:
        src = Path(src)
        kwargs['scope'] = str(os.path.realpath(src))

    # discard scanning directories and files that are not readable
    if not os.access(src, os.R_OK):
        raise OSError(f"Skipping: directory {src.path} "
                      "cannot be read by current user.")

    dst = Path(dst)

    # disable the function for src that is not a directory
    if src.is_file():
        raise NotADirectoryError(f"src {str(src)} is a file, "
                                 "pass a directory.")

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
        try:
            if ignore:
                # temporary fix fi.is_file() doesnt work when not R_OK
                if not os.access(fi, os.R_OK):
                    continue
                if fi.is_file() and ignore(fi):
                    continue

            fi_dst = dst / fi.name

            if not os.access(fi, os.R_OK):
                raise OSError(f"Skipping: {fi.path} file cannot be read.")
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
                    # times/ownership of source link are retained.
                    set_owner_mode_xattr(fi, fi_dst)

                # file outside the scope of original src
                # copy and maintain the out-of-scope symlink
                else:
                    # TODO: new symlink with absolute path?
                    shutil.copy2(fi, fi_dst, follow_symlinks=False)
                    set_owner_mode_xattr(fi, fi_dst)
            elif fi.is_dir():
                # reccursive call to copy
                copy(fi, fi_dst, ignore=ignore, logger=logger, **kwargs)
                set_owner_mode_xattr(fi, fi_dst)
            # all regular files
            # if file type is not supported for coping
            # raises error
            elif fi.is_file():
                # handle recopy
                if fi_dst.exists():
                    sstat = fi.stat()
                    dstat = fi_dst.stat()

                    sstatcmp = [sstat.st_uid, sstat.st_gid, sstat.st_mode,
                                sstat.st_size,
                                sstat.st_mtime_ns]
                    dstatcmp = [dstat.st_uid, dstat.st_gid, dstat.st_mode,
                                dstat.st_size,
                                dstat.st_mtime_ns]

                    # handle files that have only read permissions
                    # copy function needs write access
                    # so remove the file and recopy
                    if not os.access(fi_dst, os.W_OK):
                        os.unlink(fi_dst)
                        shutil.copy(fi, fi_dst, follow_symlinks=False)
                        set_owner_mode_xattr(fi, fi_dst)
                    # copy and change attributes only if files differ
                    if not sstatcmp == dstatcmp:
                        shutil.copy(fi, fi_dst, follow_symlinks=False)
                        set_owner_mode_xattr(fi, fi_dst)
                    else:
                        msg = f"Skipping: {str(fi_dst)} exists and unchanged "\
                               "to attempted copy."
                        log_or_print(msg, logger=logger)
                else:
                    shutil.copy(fi, fi_dst, follow_symlinks=False)
                    set_owner_mode_xattr(fi, fi_dst)
            else:
                msg = f"Skipping: {str(fi.path)} is a unsupported file."
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


# check already if to skip copy attempt by checking reading

def move(src, dst, ignore, logger):
    """
    dirs are created files are moved and directory is deleted if empty
    """

    src = Path(src)
    dst = Path(dst)

    # check if src and dst exist
    # and are directories

    # for
