from pathlib import Path
import tempfile
import pytest
from gar import utils
from gar import lock


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
