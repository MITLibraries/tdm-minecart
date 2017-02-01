import os
import os.path
import shutil
import tempfile

import pytest


@pytest.yield_fixture(scope="session", autouse=True)
def temp_dir():
    tmp_dir = tempfile.mkdtemp(dir=os.path.dirname(os.path.realpath(__file__)))
    tempfile.tempdir = tmp_dir
    yield tmp_dir
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)


@pytest.fixture
def clean_temp(temp_dir):
    for f in os.listdir(temp_dir):
        fpath = os.path.join(temp_dir, f)
        try:
            if os.path.isfile(fpath):
                os.unlink(fpath)
            elif os.path.isdir(fpath):
                shutil.rmtree(fpath)

        except:
            pass
