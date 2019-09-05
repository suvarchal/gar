import pytest
import os
import tempfile
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
def tempdirwithfiles(tempdir):
    """ tempdir
            |-sdir/
                |-tf2
                |-renamedlink (relative symlink to ../tf1)
            |-tf1 (5 bytes)
            |-tf2 (symlink to td/tf2)
    """
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
    yield (tempdir, sdir, tf1, tf2, renamedlink_tf1, link_tf2)
    shutil.rmtree(tempdir) if Path(tempdir).exists() else None



@pytest.fixture(scope='module')
def setup(request):
    print('\nresources_a_setup')

    def func1():
        print("func1")

    def func2():
        print("func2")
        #create_dirs(2)
    try:
        if os.environ['CI']:
            func1()
    except KeyError:
        func2()
    def teardown():
        print('teardown the setup')
    request.addfinalizer(teardown)

def create_users():
    """ Create 3 users and 2 groups """
    groups = ["group1", "group2"]
    users = {"user1": ["group1"], "user2": ["group1", "group2"], "user3": ["group2"]}
    created_groups = []
    for g in groups:
        status = os.system(f"sudo addgroup {g}")
        if status == 0:
            created_groups.append(g)
    created_users = {}
    for u, g in users.items():
        status = os.system("sudo useradd -r -m -G {} {}".format(" ".join(u),g))
        if status == 0:
            created_users.update({u, g})
    yield (created_groups, created_users)
    # clean up
    for g in created_groups:
        os.system(f"sudo groupdel {g}")
    for u,g in created_users.items():
        os.system("sudo userdel -r {u}")