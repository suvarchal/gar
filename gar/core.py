from pathlib import Path
import shutil
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


def copy(src, dst, **kwargs):
    """
    Copies from files and directories from
    `source` to `destination` retaining directory
    structure and filepermissions

    Returns None
    """
    src = Path(src)
    dst = Path(dst)
    if not dst.exists():
        os.makedirs(dst)
        set_owner_mode_xattr(src, dst)

    # a trick to send original src information to
    # recursive call of the function
    if 'scope' not in kwargs:
        kwargs['scope'] = str(src)

    # enquiring file stat on DirEntry of scandir is
    # siginiffaster then using scr.iterdir()
    for fi in os.scandir(src):
        # is destination writable?
        # is contains enough space?
        # filter for files and group
        fi_dst = dst / fi.name
        try:
            if fi.is_symlink():
                # print(fi,fi_dst)
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
                    # copies the file or dir
                    # if dir? will fail when not sudo/root
                    # because permissions need to be changed
                    if fi.is_dir():
                        print("Link SRC directory")
                        print(fi, fi.stat(), sep=':')
                        copy(fi, fi_dst)
                        set_owner_mode_xattr(fi, fi_dst)
                        print('new link dir')
                        print(fi_dst, fi_dst.stat(), sep=":")
                        print("*"*100)
                    else:
                        shutil.copy(fi, fi_dst)
                        lset_owner_mode_xattr(fi, fi_dst)
            elif fi.is_dir():
                copy(fi, fi_dst)
                set_owner_mode_xattr(fi, fi_dst)
            # for all other files, and might raise OSError
            # if file type is not supported for coping
            # sym links too if not treated properly above
            else:
                if fi.is_dir():
                    copy(fi, fi_dst)
                    continue
                shutil.copy(fi, fi_dst, follow_symlinks=False)
                set_owner_mode_xattr(fi, fi_dst)
        except Exception as ex:
            print(src, dst, ex, sep=":")
#    shutil.copytree(src, dst, ignore=ignore_me)
