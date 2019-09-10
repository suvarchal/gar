import pytest
import os
from pathlib import Path
import shutil
from gar.core import copy
from gar.utils import hash_cp_stat, hash_walk, dircmp

def test_copy(tempf, tempdir, tempdirwithfiles):
    # src has to be a directory
    with pytest.raises(NotADirectoryError):
        copy(tempf, tempf.name)

    # test copy with temp dir with files

    # create a local tempdir
    testcopydir = Path() / tempdirwithfiles.name
    os.mkdir(testcopydir)
    copy(tempdirwithfiles, testcopydir)
    print(testcopydir)
    print(tempdirwithfiles)
    #print(tempdirwithfiles.name)

    sstat=tempdirwithfiles.stat()
    dstat=testcopydir.stat()
    print(tempdirwithfiles,sstat.st_atime_ns,sstat.st_mtime_ns)
    print(testcopydir,dstat.st_atime_ns,dstat.st_mtime_ns)

    print(hash_walk(tempdirwithfiles))
    print(hash_walk(tempdirwithfiles.name))
    print(hash_walk(testcopydir))
    match,mismatch,miss = dircmp(tempdirwithfiles, testcopydir)
    print("match :",match)
    print("mismatch :",mismatch)
    print("miss :",miss)

    assert hash_walk(tempdirwithfiles) == hash_walk(testcopydir)
    assert mismatch == []
    assert miss == []
    shutil.rmtree(testcopydir)
