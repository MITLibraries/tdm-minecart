import os.path
import tempfile
import uuid

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
    with archive(archive_name) as arxv:
        for doc in docs:
            r = requests.get(doc, stream=True)
            with tempfile.NamedTemporaryFile() as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
                arxv.write(f.name, doc.name)
    return archive_name


def notify(package):
    r = requests.post(config.api + '/notify/' + package)
    r.raise_for_status()
