from collections import namedtuple

import rdflib
import requests


PCDMFile = namedtuple('PCDMFile', ['uri', 'mimetype'])
PCDM = rdflib.namespace.Namespace('http://pcdm.org/models#')
EBU = rdflib.namespace.Namespace(
        'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#')


def document_set(url, session=None, fedora=None):
    session = session or requests.Session()
    r = session.get(url)
    r.raise_for_status()
    for m in r.json().get('members'):
        doc = get_item_meta(fedora + m['ref'], session=session)
        yield Document(doc)


class Document:
    def __init__(self, graph):
        self.g = rdflib.Graph()
        self.g.parse(data=graph, format='n3')

    @property
    def files(self):
        for o in self.g.objects(subject=None, predicate=PCDM.hasFile):
            mimetype = self.g.value(subject=o, predicate=EBU.hasMimeType,
                                    object=None, any=False)
            yield PCDMFile(uri=str(o), mimetype=str(mimetype))


def get_item_meta(url, session=None):
    session = session or requests.Session()
    headers = {
        'Accept': 'text/n3',
        'Prefer': 'return=representation; '
                  'include="http://fedora.info/definitions/v4/repository'
                  '#EmbedResources"',
    }
    r = session.get(url, headers=headers)
    r.raise_for_status()
    return r.text
