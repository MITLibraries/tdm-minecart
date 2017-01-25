import os.path
import tempfile
import uuid

import requests

from minecart.config import config


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


def upload(archive):
    url = config.storage_url + '/upload' + config.bucket
    size = os.path.getsize(archive)
    filename = os.path.basename(archive)
    headers = {
        'X-Upload-Content-Type': 'application/zip',
        'X-Upload-Content-Length': size,
    }
    params = {
        'uploadType': 'resumable',
        'name': filename,
    }
    r = requests.post(url, headers=headers, params=params)
    r.raise_for_status()
    location = r.headers.get('Location')
    with open(archive, 'rb') as fp:
        headers = {
            'Content-Length': size,
            'Content-Type': 'application/zip',
        }
        r = requests.put(location, headers=headers, data=fp)
    r.raise_for_status()
    return config.storage_url + config.bucket + filename


def notify(package):
    r = requests.post(config.api + '/notify/' + package)
    r.raise_for_status()
