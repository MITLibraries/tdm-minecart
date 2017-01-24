import os

import pytest
import requests_mock

from minecart.upload import Bucket, BucketObject, Client


@pytest.yield_fixture
def google():
    with requests_mock.Mocker() as m:
        m.post('mock://example.com/b/foo/o',
               headers={'Location': 'mock://example.com/b/foo/o?upload_id=1'})
        m.put('mock://example.com/b/foo/o')
        yield m


@pytest.fixture
def package():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'fixtures/27722c0c-16f1-4c91-bf7d-9a5db7124673.zip')


def test_bucket_has_path():
    assert Bucket('foo', Client()).path == '/b/foo'


def test_bucket_has_upload_url():
    assert Bucket('foo', Client()).upload_url == \
        'https://www.googleapis.com/upload/storage/v1/b/foo/o'


def test_bucket_creates_bucket_object():
    obj = Bucket('foo', Client()).create('bar')
    assert isinstance(obj, BucketObject)


def test_bucket_object_has_url():
    assert BucketObject('bar', Bucket('foo', Client())).url == \
        'https://www.googleapis.com/storage/v1/b/foo/o/bar'


def test_bucket_uploads_from_filename(google, package):
    c = Client(url='mock://example.com', upload_url='mock://example.com')
    obj = BucketObject('bar', Bucket('foo', c))
    obj.upload(package)
    h = google.request_history
    assert h[1].method == 'PUT'
    assert h[1].qs['upload_id'] == ['1']


def test_bucket_uploads_from_file_object(google, package):
    c = Client(url='mock://example.com', upload_url='mock://example.com')
    obj = BucketObject('bar', Bucket('foo', c))
    with open(package) as fp:
        obj.upload(fp)
    h = google.request_history
    assert h[1].method == 'PUT'
    assert h[1].qs['upload_id'] == ['1']
