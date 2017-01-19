import json
import time

import jwt
import requests


class JWTAuth(requests.auth.AuthBase):
    def __init__(self, auth_url, email, key, scopes, audience):
        self.auth_url = auth_url
        self.key = key
        self.email = email
        self.scopes = scopes
        self.audience = audience
        self._token = None

    def __call__(self, r):
        if not self._token:
            self.authorize()
        r.headers['Authorization'] = 'Bearer {}'.format(self._token)
        return r

    def authorize(self):
        now = int(time.time())
        exp = now + 3600
        claims = {
            'iss': self.email,
            'scope': ' '.join(self.scopes),
            'aud': self.audience,
            'iat': now,
            'exp': exp,
        }
        msg = jwt.encode(claims, self.key, algorithm='RS256')
        data = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': msg}
        r = requests.post(self.auth_url, data=data)
        r.raise_for_status()
        resp = r.json()
        self._token = resp['access_token']


class OAuth2Session(requests.Session):
    """Self-authorizing requests session for 2-legged OAuth2.

    Use just like a normal `requests.Session` object. If a request
    returns a 401 status code it will attempt to get a token by
    calling `authorize()` on the session's auth object.

    Set the session's auth to a :class:`~minecart.oauth2.JWTAuth` object::

        s = OAuth2Session()
        s.auth = JWTAuth(...)
        s.get(some_url)

    """
    def request(self, *args, **kwargs):
        resp = super(OAuth2Session, self).request(*args, **kwargs)
        if resp.status_code == 401:
            self.auth.authorize()
            resp = super(OAuth2Session, self).request(*args, **kwargs)
        return resp
