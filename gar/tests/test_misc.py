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


