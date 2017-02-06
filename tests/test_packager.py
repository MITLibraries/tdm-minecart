from unittest import mock
import os
import tempfile
import zipfile

import pytest
import requests
import requests_mock
from rdflib import URIRef, namespace

from minecart.packager import (document_set, get_item_meta, Document,
                               create_package, handle_message, ApiListener)
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
        m.get('mock://example.com/api', json={'members': [{'ref': '123'},
                                                          {'ref': '456'}]})
        m.get('mock://example.com/fedora/thesis/123', text=thesis_1)
        m.get('mock://example.com/fedora/thesis/456', text=thesis_2)
        m.get('mock://example.com/baz', content=thesis_1_pdf)
        m.get('mock://example.com/quux', content=thesis_2_pdf)
        m.post('mock://example.com/google/b/foo/o',
               headers={'Location': 'mock://example.com/google/b/foo/o?'
                                    'upload_id=1'})
        m.put('mock://example.com/google/b/foo/o')
        yield m


def test_document_set_generates_documents(webmock):
    dset = document_set('mock://example.com/api',
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
    pkg = create_package('mock://example.com/api',
                         fedora='mock://example.com/fedora/thesis/')
    with zipfile.ZipFile(pkg) as zf:
        members = zf.namelist()
    assert all([f in members for f in ('123.pdf', '456.pdf')])


def test_api_listener_passes_context():
    with mock.patch('minecart.packager.handle_message') as m:
        bucket = mock.Mock()
        session = mock.Mock()
        listener = ApiListener('mock://example.com/fedora', bucket, session)
        listener.on_message({}, 'foobar')
        m.assert_called_with('foobar', {'fedora': 'mock://example.com/fedora',
                                        'bucket': bucket, 'http': session})


def test_handle_message_uploads_package(webmock):
    bucket = Client(upload_url='mock://example.com/google').get('foo')
    handle_message('{"docset": "mock://example.com/api"}',
                   {'fedora': 'mock://example.com/fedora/thesis/',
                    'bucket': bucket, 'http': requests.Session()})
    assert webmock.request_history[-1].method == 'PUT'


def test_handle_message_deletes_archive(webmock, clean_temp):
    bucket = Client(upload_url='mock://example.com/google').get('foo')
    handle_message('{"docset": "mock://example.com/api"}',
                   {'fedora': 'mock://example.com/fedora/thesis/',
                    'bucket': bucket, 'http': requests.Session()})
    assert not os.listdir(tempfile.tempdir)
