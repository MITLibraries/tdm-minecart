import os.path
import tempfile
import uuid
import zipfile

import requests


def docset(docset_id):
    r = requests.get(config.api + '/docsets/' + docset_id + '/catalog')
    r.raise_for_status()
    return r.jsoin().get('docs')


def create_archive(docs):
    """Create a zip archive of a docset.

    Note that each document is read into memory before being written. If you
    are writing large files this could be a problem.
    """
    tmp = tempfile.gettempdir()
    archive_name = os.path.join(tmp, uuid.uuid4()) + '.zip'
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            r = requests.get(doc)
            zf.writestr(doc, r.content)
    return archive_name


def notify(package):
    r = requests.post(config.api + '/notify/' + package)
    r.raise_for_status()
