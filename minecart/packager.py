from collections import namedtuple
import json
import logging
import os.path
import tempfile
import uuid

import rdflib
import requests
import stomp

from minecart.archive import archive


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
        yield Document(m['ref'], doc)


class Document:
    def __init__(self, name, graph):
        self.g = rdflib.Graph()
        self.g.parse(data=graph, format='n3')
        self.name = name

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


def create_package(url, session=None, fedora=None):
    session = session or requests.Session()
    tmp = tempfile.gettempdir()
    archive_name = os.path.join(tmp, uuid.uuid4().hex) + '.zip'
    with archive(archive_name) as arxv:
        for doc in document_set(url, session, fedora):
            for f in doc.files:
                if f.mimetype == 'application/pdf':
                    r = session.get(f.uri, stream=True)
                    r.raise_for_status()
                    with tempfile.NamedTemporaryFile() as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            f.write(chunk)
                        arxv.write(f.name, doc.name + '.pdf')
    return archive_name


class ApiListener(stomp.ConnectionListener):
    def __init__(self, fedora_url, bucket, session):
        self.ctx = {
            'fedora': fedora_url,
            'bucket': bucket,
            'http': session,
        }

    def on_message(self, headers, message):
        handle_message(message, self.ctx)


def handle_message(message, ctx):
    logger = logging.getLogger(__name__)
    bucket = ctx['bucket']
    session = ctx['http']
    msg = json.loads(message)
    try:
        arxv = create_package(msg['docset'], session=session,
                              fedora=ctx['fedora'])
        blob = bucket.create(os.path.basename(arxv))
        blob.upload(arxv)
        # notify_api(blob.url)
    except Exception:
        logger.error("Could not create package for docset: {}".
                     format(msg['docset']))
    finally:
        os.remove(arxv)
