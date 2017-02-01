import pytest
import requests_mock
from rdflib import URIRef, namespace

from minecart.packager import document_set, get_item_meta, Document


BIBO = namespace.Namespace('http://purl.org/ontology/bibo/')


@pytest.fixture(scope='session')
def thesis_1():
    with open('tests/fixtures/thesis_1.n3') as f:
        return f.read()


@pytest.fixture(scope='session')
def thesis_2():
    with open('tests/fixtures/thesis_2.n3') as f:
        return f.read()


@pytest.yield_fixture
def webmock(thesis_1, thesis_2):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com/api', json={'members': [{'ref': '123'},
                                                          {'ref': '456'}]})
        m.get('mock://example.com/fedora/thesis/123', text=thesis_1)
        m.get('mock://example.com/fedora/thesis/456', text=thesis_2)
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
    doc = Document(thesis_1)
    files = list(doc.files)
    assert ('mock://example.com/bar', 'text/plain') in files
    assert ('mock://example.com/baz', 'application/pdf') in files
