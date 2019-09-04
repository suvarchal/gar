from pathlib import Path
import shutil
from shutil import SameFileError, SpecialFileError
import os


def set_owner_mode_xattr(src, dst):
    # src = Path(src)
    # dst = Path(dst)
    src_stat = src.stat()
    os.chown(dst, src_stat.st_uid, src_stat.st_gid)
    os.chmod(dst, mode=src_stat.st_mode)
    os.utime(dst, ns=(src_stat.st_atime_ns, src_stat.st_mtime_ns))
    shutil._copyxattr(src, dst)


def lset_owner_mode_xattr(src, dst):
    # src = Path(src)
    # dst = Path(dst)
    src_stat = src.stat()
    os.chown(dst, src_stat.st_uid, src_stat.st_gid, follow_symlinks=False)
    os.chmod(dst, mode=src_stat.st_mode)
    os.utime(dst, ns=(src_stat.st_atime_ns, src_stat.st_mtime_ns), follow_symlinks=False)
    shutil._copyxattr(src, dst, follow_symlinks=False)


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
    if not dst.exists():
        os.makedirs(dst)
        # try block?
        set_owner_mode_xattr(src, dst)

    # a trick to send original src information to
    # recursive call of the function
    if 'scope' not in kwargs:
        kwargs['scope'] = str(src)

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
                    lset_owner_mode_xattr(fi, fi_dst)
            
                # file outside scope of original src
                else:
                    # maintain the out-of-scope symlink
                    shutil.copy(fi, fi_dst, follow_symlinks=False)
                    lset_owner_mode_xattr(fi, fi_dst)
            elif fi.is_dir():
                # reccursive call to copy
                copy(fi, fi_dst)
                set_owner_mode_xattr(fi, fi_dst)
            # all files
            # if file type is not supported for coping
            # raises error
            else:
                shutil.copy(fi, fi_dst, follow_symlinks=False)
                set_owner_mode_xattr(fi, fi_dst)

        except (SameFileError, SpecialFileError) as ex:
            logger.warn(f"Skipping: {ex.filename}")

        except (OSError, PermissionError) as ex:
            msg = "Do you have enough permissions to change file ownership?\n"\
                  "Run as privilaged user or see `gar --help` for options."
            logger.error(f"{fi.path} to {fi_dst} {ex} \n{msg} ")

        except IOError as ex:
            if logger:
                logger.critical(ex)
            else:
                print(ex)

