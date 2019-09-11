import pytest
import os
import tempfile
import pwd
import grp
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
            |-tf3 (file with permissions 640 )
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
        # file with permissions 640
        _, tf3 = tempfile.mkstemp(dir=tempdir)
        Path(tf3).write_bytes(b"tempo")
        os.chmod(tf3, 0o640)
        if user:
            gid = pwd.getpwnam(user).pw_gid
            group_name = grp.getgrnam(gid).gr_name
            status = os.system(f"sudo chown -R {sdir} {user}:{group_name}")
            assert status == 0
            status = os.system(f"sudo chown {tf1} {user}:{group_name}")
            assert status == 0
            status = os.system(f"sudo chown {tf2} {user}:{group_name}")
            assert status == 0
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
            groups_str = " ".join(g) if len(g)>1 else g
            status = os.system("sudo useradd -r -m -G {} {}".format(groups_str, u))
            if status == 0:
                created_users.append(u)
        yield (created_groups, created_users)
        # clean up
        for g in created_groups:
            os.system(f"sudo groupdel {g}")
        for u in created_users:
            os.system(f"sudo userdel -r {u}")
    else:
        yield None
