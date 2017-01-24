import os.path

import requests


class Client:
    def __init__(self, session=None,
                 url='https://www.googleapis.com/storage/v1',
                 upload_url='https://www.googleapis.com/upload/storage/v1'):
        self.session = session or requests.Session()
        self.url = url
        self.upload_url = upload_url

    def get(self, bucket):
        return Bucket(bucket, client=self)

    def request(self, method, url, **kwargs):
        return self.session.request(method, url, **kwargs)


class Bucket:
    def __init__(self, name, client):
        self.name = name
        self.client = client

    @property
    def path(self):
        return '/b/' + self.name

    @property
    def url(self):
        return self.client.url + self.path

    @property
    def upload_url(self):
        return self.client.upload_url + self.path + '/o'

    def create(self, obj_name):
        return BucketObject(obj_name, bucket=self)


class BucketObject:
    def __init__(self, name, bucket):
        self.name = name
        self.bucket = bucket
        self.client = bucket.client

    @property
    def url(self):
        return self.bucket.url + '/o/' + self.name

    def upload(self, file_obj):
        if isinstance(file_obj, str):
            with open(file_obj, 'rb') as f:
                self._upload_bytes(f)
        else:
            self._upload_bytes(file_obj)

    def _upload_bytes(self, fp):
        size = os.fstat(fp.fileno()).st_size
        location = self._resumable_session(size)
        resp = self.client.request('PUT', location, data=fp)
        resp.raise_for_status()

    def _resumable_session(self, filesize):
        headers = {
            'X-Upload-Content-Type': 'application/zip',
            'X-Upload-Content-Length': str(filesize),
            'Content-Length': '0',
        }
        params = {
            'uploadType': 'resumable',
            'name': self.name,
        }
        resp = self.client.request('POST', self.bucket.upload_url,
                                   headers=headers, params=params)
        if resp.status_code != 200:
            raise Exception('Error creating resumable session')
        return resp.headers['Location']
