import pytest
import os
from pathlib import Path
import shutil
from gar.core import copy, gcopy, verify
from gar.utils import hash_cp_stat, hash_walk, dircmp, cp_stat
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

    # test recopy
    # save prev hash
    prev_copy_hash = hash_walk(testcopydir)
    copy(tempdirwithfiles, testcopydir)
    new_copy_hash = hash_walk(testcopydir)
    # check no changes
    _, mismatch, miss = dircmp(tempdirwithfiles, testcopydir)
    print("in recopy")
    if not mismatch == []:
        for f in mismatch:
            print(f"{f[1]}: {cp_stat(f[1])}", f"{f[2]}: {cp_stat(f[2])}")
    
    # assert prev_copy_hash == new_copy_hash
    print("in recopy",miss)
    if not miss == []:
        for f in miss:
            print(os.system(f"ls -lrt {f[0]}"))
            print(os.system(f"ls -lrt {f[1]}"))
    assert mismatch == []
    assert miss == []

    #print(tempdirwithfiles.name)

    shutil.rmtree(testcopydir)


def test_gcopy(tempdirwithfiles):
    user = os.getlogin() or os.getenv("USER")
    testcopydir = Path() / tempdirwithfiles.name
    testcopydir.mkdir()
    gcopy(user, tempdirwithfiles, testcopydir)
    
    match, mismatch, miss = dircmp(tempdirwithfiles, testcopydir)
    print("match :", match)
    print("mismatch :", mismatch)
    print("miss :", miss)
    if not mismatch == []:
        for f in mismatch:
            print(f"{f[1]}: {os.stat(f[1])}", f"{f[2]}: {os.stat(f[2])}")
    #assert hash_walk(tempdirwithfiles) == hash_walk(testcopydir)
    assert mismatch == []
    assert miss == []
    shutil.rmtree(testcopydir)
    # for copy verify if miss == 0
    # for recopy verify if previous hash is same
    # for move verify new files dont exist by gwalk


def test_verify(tempdirwithfiles):
    tempdircopy = Path() / tempdirwithfiles.name
    tempdircopy.mkdir()
    copy(tempdirwithfiles, tempdircopy)
    compare = verify(str(tempdirwithfiles), str(tempdircopy))
    assert isinstance(compare, dict)
    print(compare)
    assert compare['Mismatch'] == []
    assert compare['Miss'] == []
    shutil.rmtree(tempdircopy)
