import os
from pathlib import Path
import tempfile
import hashlib
import shutil
import pytest
from gar import utils
from gar import lock
from gar.logger import syslogpath, rotator, setup_logger


# Fixture: Create a temp file
@pytest.fixture
def tempf():
    """ Create a tempfile write 5 bytes
    """
    _, tempf = tempfile.mkstemp()
    tempf = Path(tempf)
    # make a temp file with 5 bytes
    tempf.write_bytes(b"tempo")
    yield tempf
    tempf.unlink() if tempf.exists() else None


# test group utils
def test_gid_utils(tempf):
    tfile_gid = tempf.stat().st_gid
    assert utils.getgid(tfile_gid) == tfile_gid

    # hr_fstat = utils.hr_filestat(tempf)
    # assert utils.getgid(hr_fstat['Group']) == tfile_gid

    gm = utils.group_members("root")
    assert "root" in gm


# test lock functions
@pytest.fixture
def templock():
    templock = lock.lockpath / "gartest.lock"
    yield templock
    templock.unlink() if templock.exists() else None


def test_lock_simplelock(templock):
    with lock.SimpleFileLock(templock):
        assert templock.exists()
        with pytest.raises(OSError):
            sff = lock.SimpleFileLock(templock)
            sff.__enter__()


def test_lock_filelock(templock):
    with lock.FileLock(templock):
        assert templock.exists()
        with pytest.raises(OSError):
            fl = lock.FileLock(templock)
            fl.__enter__()

# Test logging functions
@pytest.fixture
def temp_log():
    log_src = Path("gartemplog")
    log_src.write_text("log")
    log_dst = Path(f"{log_src.name}.gz")
    yield log_src, log_dst
    log_src.unlink() if log_src.exists() else None
    log_dst.unlink() if log_dst.exists() else None


def test_logger_rotator(temp_log):
    # second argument file will be appended by .gz internally
    rotator(temp_log[0], temp_log[0])
    assert not temp_log[0].exists()
    assert temp_log[1].exists()

# test file utils of gar.utils
@pytest.fixture
def tempf():
    """ Create a tempfile write 5 bytes
    """
    _, tempf = tempfile.mkstemp()
    tempf = Path(tempf)
    # make a temp file with 5 bytes
    tempf.write_bytes(b"tempo")
    yield tempf
    tempf.unlink() if tempf.exists() else None

@pytest.fixture
def tempsym(tempf):
    """ Create a symlink to a tempfile
    note chaining fixtures tempsym and tempf
    """
    symf = Path("tempsymf")
    os.symlink(tempf, symf)
    yield symf, tempf
    symf.unlink() if symf.exists() else None

@pytest.fixture
def tempdir():
    """ Create a tmp directory """
    td = tempfile.mkdtemp()
    td = Path(td)
    yield td
    shutil.rmtree(td) if td.exists() else None

@pytest.fixture
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


def test_filestat(tempf):
    """ checks utils.cp_filestat, utils.hr_size """
    assert utils.cp_filestat(tempf)['Size'] == tempf.stat().st_size
    hr_fstat = utils.hr_filestat(tempf)
    assert utils.hr_size(tempf.stat().st_size) == utils.hr_size(5)
    assert tempf.stat().st_dev == hr_fstat['Device']
    assert "MB" in utils.hr_size(10**7)

    # check for filestat
    cp_fstat = utils.cp_filestat(tempf)
    assert tempf.name == cp_fstat['Name']

    # check for sting input
    cp_fstat = utils.cp_filestat(str(tempf))
    assert tempf.name == cp_fstat['Name']

    # check if cp_stat, cp_filestat are same
    cp_fstat2 = utils.cp_stat(tempf)
    assert cp_fstat == cp_fstat2

    # copy as same user and check stat
    tempfcopy = tempf.name
    shutil.copy2(tempf, tempfcopy)
    s1 = utils.cp_stat(tempf)
    s2 = utils.cp_stat(tempfcopy)
    assert s1 == s2 

    # tempf is not a link or dir
    assert utils.cp_linkstat(tempf) is None
    assert utils.cp_dirstat(tempf) is None


def test_symlink(tempsym):
    symf, tempf = tempsym

    #check if symlink and target are not same
    lstat = utils.cp_stat(symf)
    lstat2 = utils.cp_stat(tempf)
    assert not lstat == lstat2

    # check follow links is same as target
    lstat = utils.cp_stat(tempf, follow_symlinks=True)
    assert lstat == lstat2


def test_hash_utils(tempf, tempsym, tempdirwithfiles):
    """ Check if hashing functions work
    as intended, very important for
    verifying integrity of copy/move
    """

    # copy file and check
    tempfcopy = tempf.name
    shutil.copy2(tempf, tempfcopy)
    h1 = utils.hash_cp_stat(tempf)
    h2 = utils.hash_cp_stat(tempfcopy)
    assert h1 == h2
    os.unlink(tempfcopy)
    
    # check hash works for directories with files
    #h1 = hashlib.sha1()
    h1 = utils.hash_walk(tempdirwithfiles[0])
    #assert not h1 == h2[0]

    tempdcopy = Path("tmpdircopy")
    shutil.rmtree(tempdcopy) if tempdcopy.exists() else None

    shutil.copytree(tempdirwithfiles[0], tempdcopy, symlinks=True)
    h2 = utils.hash_walk(tempdcopy)
    
    from functools import reduce
    h1sum = reduce(lambda x, y: x ^ y, h1.values())

    h2sum = reduce(lambda x, y: x ^ y, h2.values())
    assert h1sum == h2sum

    shutil.rmtree(tempdcopy)
