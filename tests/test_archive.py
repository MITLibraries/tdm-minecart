import os
import tempfile
import zipfile

import pytest

from minecart.archive import archive, Zip


@pytest.yield_fixture
def thesis():
    with tempfile.NamedTemporaryFile() as t:
        t.write(b'foobar')
        t.flush()
        yield t.name


def test_zip_writes_file_to_archive(thesis):
    with tempfile.TemporaryFile() as fp:
        arx = Zip(fp)
        arx.write(thesis, 'test.txt')
        arx.close()
        with zipfile.ZipFile(fp) as zf:
            assert b'foobar' == zf.read('test.txt')


def test_archive_returns_writeable_archive(thesis):
    with tempfile.NamedTemporaryFile() as fp:
        with archive(fp.name) as arx:
            arx.write(thesis, 'test.txt')
        with zipfile.ZipFile(fp) as zf:
            assert 'test.txt' in zf.namelist()


def test_archive_deletes_archive_on_error():
    fp = tempfile.NamedTemporaryFile()
    with pytest.raises(Exception):
        with archive(fp.name):
            raise Exception
    assert not os.path.isfile(fp.name)
