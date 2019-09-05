import pytest
import os
import tempfile
import pwd
import shutil
from pathlib import Path


@pytest.fixture(scope="function")
def tempf():
    """ Create a tempfile write 5 bytes
    """
    _, tempf = tempfile.mkstemp()
    tempf = Path(tempf)
    # make a temp file with 5 bytes
    tempf.write_bytes(b"tempo")
    yield tempf
    tempf.unlink() if tempf.exists() else None

@pytest.fixture(scope="function")
def tempsym(tempf):
    """ Create a symlink to a tempfile
    note chaining fixtures tempsym and tempf
    """
    symf = Path("tempsymf")
    os.symlink(tempf, symf)
    yield symf, tempf
    symf.unlink() if symf.exists() else None
    tempf.unlink() if tempf.exists() else None

@pytest.fixture(scope="function")
def tempdir():
    """ Create a tmp directory """
    td = tempfile.mkdtemp()
    td = Path(td)
    yield td
    shutil.rmtree(td) if td.exists() else None

@pytest.fixture(scope="function")
def tempdirwithfiles(tempdir, create_users):
    """ tempdir
            |-sdir/
                |-tf2
                |-renamedlink (relative symlink to ../tf1)
            |-tf1 (5 bytes)
            |-tf2 (symlink to td/tf2)
    """
    def create_files(user=None):
        sdir = tempfile.mkdtemp(dir=tempdir)
        _, tf1 = tempfile.mkstemp(dir=tempdir)
        Path(tf1).write_bytes(b"tempo")
        # a file inside td
        _, tf2 = tempfile.mkstemp(dir=sdir)
        # relative symlink
        renamedlink_tf1 = Path(sdir) / "renamedlink_tf1"
        os.symlink(f"../{Path(tf1).name}", renamedlink_tf1)
        # abs symlink
        link_tf2 = Path(tempdir)/Path(tf2).name
        os.symlink(tf2, link_tf2)
        if user:
            upwd = pwd.getpwnam(user)
            uid = upwd.pw_uid
            gid = upwd.pw_gid
            os.chown(sdir, uid, gid, follow_symlinks=False)
            os.chown(tf1, uid, gid, follow_symlinks=False)
            os.chown(tf2, uid, gid, follow_symlinks=False)
            os.chown(renamedlink_tf1, uid, gid, follow_symlinks=False)
            os.chown(link_tf2, uid, gid, follow_symlinks=False)
        return (tempdir, sdir, tf1, tf2, renamedlink_tf1, link_tf2)
    if create_users:
        (groups, users) = create_users
        for user in users:
            create_files(user=user)
        yield tempdir
    else:
        create_files()
        yield tempdir
    # cleanup not necessary because tempdir is cleaned up anyway
    # shutil.rmtree(tempdir) if Path(tempdir).exists() else None

@pytest.fixture(scope="session")
def create_users():
    """ Create 3 users and 2 groups """
    # if in CI or root
    if os.environ.get('CI') or os.access("/", os.W_OK):
        groups = ["group1", "group2"]
        users = {"user1": ["group1"], "user2": ["group1", "group2"], "user3": ["group2"]}
        created_groups = []
        for g in groups:
            status = os.system(f"sudo addgroup {g}")
            if status == 0:
                created_groups.append(g)
        created_users = []
        for u, g in users.items():
            status = os.system("sudo useradd -r -m -G {} {}".format(" ".join(g),u))
            if status == 0:
                created_users.append(u)
        yield (created_groups, created_users)
        # clean up
        for g in created_groups:
            os.system(f"sudo groupdel {g}")
        for u, g in created_users.items():
            os.system("sudo userdel -r {u}")
    else:
        yield None
