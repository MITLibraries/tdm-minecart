from unittest import mock

import jwt
import pytest
import requests_mock
import requests

from minecart.oauth2 import JWTAuth, OAuth2Session


@pytest.yield_fixture
def google():
    with requests_mock.Mocker() as m:
        m.post('mock://example.com', json={'access_token': 'good job!'})
        yield m


@pytest.fixture(scope="session")
def private_key():
    with open('tests/fixtures/id_rsa') as fp:
        key = fp.read()
    return key


@pytest.fixture(scope="session")
def public_key():
    with open('tests/fixtures/id_rsa.pub') as fp:
        key = fp.read()
    return key


@pytest.fixture
def auth(private_key):
    return JWTAuth('mock://example.com', 'foo@example.com', private_key,
                   ['http://example.com/scope'], 'http://example.com/aud')


def test_jwtauth_authorizes_on_first_call(google, auth):
    auth(mock.MagicMock())
    assert google.called


def test_jwtauth_sets_authorization_header(google, auth):
    req = auth(mock.MagicMock())
    req.headers.__setitem__.assert_called_with('Authorization',
                                               'Bearer good job!')


def test_jwtauth_only_authorizes_if_no_token(google, auth):
    auth(mock.MagicMock())
    auth(mock.MagicMock())
    assert google.call_count == 1


def test_jwtauth_adds_data_to_auth_request(google, auth, public_key):
    auth(mock.MagicMock())
    req = google.request_history[0]
    body = dict(p.split('=') for p in req.text.split('&'))
    msg = jwt.decode(body['assertion'], key=public_key, verify=False)
    assert body['grant_type'] == \
        'urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer'
    assert msg['iss'] == 'foo@example.com'
    assert msg['aud'] == 'http://example.com/aud'
    assert msg['scope'] == 'http://example.com/scope'


def test_oauth2_session_authorizes_on_first_use(google, auth):
    google.get('mock://example.com/bucket/1')
    s = OAuth2Session()
    s.auth = auth
    s.get('mock://example.com/bucket/1')
    assert google.call_count == 2
    assert google.request_history[0].method == 'POST'


def test_oauth2_session_authorizes_on_401(google, auth):
    google.get('mock://example.com/bucket/1',
               [{'status_code': 401}, {'status_code': 200}])
    s = OAuth2Session()
    s.auth = auth
    s.auth._token = 'my voice is my passport'
    resp = s.get('mock://example.com/bucket/1')
    assert google.call_count == 3
    assert google.request_history[1].method == 'POST'


def test_oauth2_session_skips_auth_when_session_valid(google, auth):
    google.get('mock://example.com/bucket/1')
    s = OAuth2Session()
    s.auth = auth
    s.auth._token = 'my voice is my passport'
    s.get('mock://example.com/bucket/1')
    assert google.call_count == 1

