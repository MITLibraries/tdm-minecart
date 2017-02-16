import os
import re
import tempfile
from unittest import mock
import zipfile

import pytest
import requests_mock
from rdflib import URIRef, namespace

from minecart.packager import (document_set, get_item_meta, Document,
                               create_package, ApiListener)
from minecart.upload import Client


BIBO = namespace.Namespace('http://purl.org/ontology/bibo/')


@pytest.fixture(scope='session')
def thesis_1():
    with open('tests/fixtures/thesis_1.n3') as f:
        return f.read()


@pytest.fixture(scope='session')
def thesis_1_pdf():
    with open('tests/fixtures/thesis_1.pdf', 'rb') as f:
        return f.read()


@pytest.fixture(scope='session')
def thesis_2_pdf():
    with open('tests/fixtures/thesis_2.pdf', 'rb') as f:
        return f.read()


@pytest.fixture(scope='session')
def thesis_2():
    with open('tests/fixtures/thesis_2.n3') as f:
        return f.read()


@pytest.yield_fixture
def webmock(thesis_1, thesis_2, thesis_1_pdf, thesis_2_pdf):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com/docset/1',
              json={'members': [{'ref': '123'}, {'ref': '456'}]})
        m.get('mock://example.com/fedora/thesis/123', text=thesis_1)
        m.get('mock://example.com/fedora/thesis/456', text=thesis_2)
        m.get('mock://example.com/baz', content=thesis_1_pdf)
        m.get('mock://example.com/quux', content=thesis_2_pdf)
        m.post('mock://example.com/google/b/foo/o',
               headers={'Location': 'mock://example.com/google/b/foo/o?'
                                    'upload_id=1'})
        m.put('mock://example.com/google/b/foo/o')
        yield m


@pytest.fixture
def listener():
    bucket = Client(url='mock://example.com/google',
                    upload_url='mock://example.com/google').get('foo')
    return ApiListener(fedora='mock://example.com/fedora/thesis/',
                       bucket=bucket,
                       conn=mock.MagicMock())


def test_document_set_generates_documents(webmock):
    dset = document_set('mock://example.com/docset/1',
                        fedora='mock://example.com/fedora/thesis/')
    d1 = next(dset)
    d2 = next(dset)
    assert d1.g.value(subject=URIRef('mock://example.com/1'),
                      predicate=BIBO.handle) == URIRef('http://handle.org/1')
    assert d2.g.value(subject=URIRef('mock://example.com/2'),
                      predicate=BIBO.handle) == URIRef('http://handle.org/2')


def test_get_item_meta_returns_rdf_metadata(webmock, thesis_1):
    rdf = get_item_meta('mock://example.com/fedora/thesis/123')
    assert rdf == thesis_1


def test_document_generates_file_objects(thesis_1):
    doc = Document('foobar', thesis_1)
    files = list(doc.files)
    assert ('mock://example.com/bar', 'text/plain') in files
    assert ('mock://example.com/baz', 'application/pdf') in files


def test_create_package_returns_archive(webmock):
    pkg = create_package('mock://example.com/docset/1',
                         fedora='mock://example.com/fedora/thesis/')
    with zipfile.ZipFile(pkg) as zf:
        members = zf.namelist()
    assert all([f in members for f in ('123.pdf', '456.pdf')])


def test_on_message_uploads_package(webmock, listener):
    listener.on_message(None, 'mock://example.com/docset/1')
    assert webmock.request_history[-1].method == 'PUT'
    assert webmock.request_history[-1].url == \
        'mock://example.com/google/b/foo/o?upload_id=1'


def test_on_message_deletes_archive(webmock, clean_temp, listener):
    listener.on_message(None, 'mock://example.com/docset/1')
    assert not os.listdir(tempfile.tempdir)


def test_on_message_deletes_package_after_error(webmock, clean_temp, listener):
    webmock.put('mock://example.com/google/b/foo/o', status_code=500)
    listener.on_message(None, 'mock://example.com/docset/1')
    assert not os.listdir(tempfile.tempdir)


def test_listener_does_not_die_on_error_creating_package(webmock, listener):
    webmock.get('mock://example.com/docset/1', status_code=500)
    listener.on_message(None, 'mock://example.com/docset/1')


def test_on_message_accepts_package_request(webmock, listener):
    listener.on_message(None, 'mock://example.com/docset/1')
    args = listener.conn.send.call_args_list[0][0]
    assert args[0] == '/queue/package/1'
    assert args[1] == 'Accepted.'


def test_on_message_notifies_queue_with_url_and_size(webmock, listener):
    listener.on_message(None, 'mock://example.com/docset/1')
    args = listener.conn.send.call_args[0]
    assert args[0] == '/queue/package/1'
    assert re.match(r'Complete: mock://example.com/google/b/foo/o/'
                    r'\w+.zip\nSize: \d+', args[1])
