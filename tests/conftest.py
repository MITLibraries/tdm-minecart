import os.path
import shutil
import tempfile

import pytest


@pytest.yield_fixture(scope="session", autouse=True)
def temp_dir():
    tmp_dir = tempfile.mkdtemp(dir=os.path.dirname(os.path.realpath(__file__)))
    tempfile.tempdir = tmp_dir
    yield
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
