import pytest
import os
from pathlib import Path
import random
import string


def create_dirs(numdirs=1, basedir="."):
    for nd in range(numdirs):
        if not Path(basedir).exists():
            Path(basedir).mkdir()
        dpath = "".join(random.choice(string.ascii_lowercase) 
                        for x in range(5))
        print(dpath)
        (Path(basedir) / dpath).mkdir()


@pytest.fixture(scope='module')
def setup(request):
    print('\nresources_a_setup')

    def func1():
        print("func1")

    def func2():
        print("func2")
        create_dirs(2)
    try:
        if os.environ['CI']:
            func1()
    except KeyError:
        func2()

    def teardown():
        print('teardown the setup')
    request.addfinalizer(teardown)

    def create_groups_users():
        """ Create 5 users and x groups """
        groups = ["group1","group2"]
        users  = {"user1":["group1"],"user2":["group1","group2"],"user3":["group2"]}
        for g in groups:
            os.system("add group ".format(g))
        for u,g in users.items():
            "useradd -r -m -G {} {}".format(" ".join(v),k)
