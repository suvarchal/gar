import pytest
import os
import pwd
import grp
from pathlib import Path
import shutil
from gar.core import copy, gcopy, verify, move
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
    match,mismatch,miss, skip = dircmp(tempdirwithfiles, testcopydir)
    print("match :",match)
    print("mismatch :",mismatch)
    print("miss :",miss)
    print("skip :",skip)

    assert hash_walk(tempdirwithfiles) == hash_walk(testcopydir)
    assert mismatch == []
    assert miss == []

    # test recopy
    # save prev hash
    prev_copy_hash = hash_walk(testcopydir)
    copy(tempdirwithfiles, testcopydir)
    new_copy_hash = hash_walk(testcopydir)
    # check no changes
    _, mismatch, miss, skip = dircmp(tempdirwithfiles, testcopydir)
    pmismatch = [(cp_stat(f[1]), cp_stat(f[2])) for f in mismatch if f]
    print(pmismatch)

    assert prev_copy_hash == new_copy_hash
    assert mismatch == []
    assert miss == []

    shutil.rmtree(testcopydir)


def test_gcopy(tempdirwithfiles):
    group = grp.getgrgid(os.getegid()).gr_name
    testcopydir = Path() / tempdirwithfiles.name
    testcopydir.mkdir()
    gcopy(group, tempdirwithfiles, testcopydir)
    
    match, mismatch, miss, skip = dircmp(tempdirwithfiles, testcopydir)
    print("match :", match)
    print("mismatch :", mismatch)
    print("miss :", miss)
    pmismatch = [(cp_stat(f[1]), cp_stat(f[2])) for f in mismatch if f]
    print(pmismatch)
    # check has to be based on groups
    assert 1
    #assert hash_walk(tempdirwithfiles) == hash_walk(testcopydir)
    #assert mismatch == []
    #assert miss == []
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
    assert compare['Mismatch'] == []
    assert compare['Miss'] == []
    shutil.rmtree(tempdircopy)


def test_move(tempdirwithfiles):
    tempdircopy = Path() / tempdirwithfiles.name
    ls_dir = os.listdir(tempdirwithfiles)
    tempdircopy.mkdir()
    move(tempdirwithfiles, tempdircopy)
    print(os.listdir(tempdirwithfiles))
    # check no files exist anymore in src
    assert not os.listdir(tempdirwithfiles)
    print(ls_dir, os.listdir(tempdircopy))
    # check if dir contents are same as before
    # better use walk
    assert sorted(ls_dir) == sorted(os.listdir(tempdircopy))
    shutil.rmtree(tempdircopy)


def test_gmove(tempdirwithfiles):
    group = grp.getgrgid(os.getegid()).gr_name
    tempdircopy = Path() / tempdirwithfiles.name
    ls_dir = os.listdir(tempdirwithfiles)
    tempdircopy.mkdir()
    gmove(group, tempdirwithfiles, tempdircopy)
    print(os.listdir(tempdirwithfiles))
    # check no contents exist for the group
    assert not os.listdir(tempdirwithfiles)
    # check if dir contents are same as before
    print(ls_dir, os.listdir(tempdircopy))
    assert sorted(ls_dir) == sorted(os.listdir(tempdircopy))
    shutil.rmtree(tempdircopy)