import pytest
import os
#from .copy import copy

class TestCopy:
    #def setup_class(self):
    #    print("setup")

    #def teardown_method(self):
    #    print("teardown")
    def test_copy(self):
        print('hello')
        assert 0
    @pytest.mark.multiuser
    def test_copy_whatever(self):
        print("in multiuser")
        assert 1
    def test_new(self,setup):
        print("hello in proces")
        assert 0
    def test_new2(self,setup):
        print("heello in 2")
        assert 0
 #   def test_copyit(self):
 #       print('done copy')
 #       assert 0

#@pytest.mark.slow
#def test_none():
#    print("hello")
#    assert 0