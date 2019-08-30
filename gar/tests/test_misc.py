from pathlib import Path
import pytest
from gar import lock

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
