# -*- coding: utf-8 -*-

#  This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.

"""
HTTP compatibility layer using httpx.

This module provides a requests-compatible API using httpx as the backend.
Use this instead of importing requests directly.
"""

import httpx
from httpx import (
    ConnectionError,
    HTTPError,
    RequestException,
    SSLError,
    Timeout,
)

# For backward compatibility, expose common exception classes
__all__ = [
    'requests',
    'ConnectionError',
    'HTTPError',
    'RequestException',
    'SSLError',
    'Timeout',
]


class _RequestsCompatResponse:
    """
    Wraps httpx.Response to provide requests-compatible interface.
    """

    def __init__(self, response: httpx.Response):
        self._response = response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def content(self) -> bytes:
        return self._response.content

    @property
    def text(self) -> str:
        return self._response.text

    @property
    def headers(self) -> dict:
        return dict(self._response.headers)

    def json(self, **kwargs):
        return self._response.json(**kwargs)

    def raise_for_status(self):
        self._response.raise_for_status()

    def __getattr__(self, name):
        # Delegate to underlying response for any other attributes
        return getattr(self._response, name)


class _RequestsCompatSession:
    """
    Wraps httpx.Client to provide requests.Session-compatible interface.
    """

    def __init__(self, **kwargs):
        self._client = httpx.Client(**kwargs)

    def request(self, method, url, **kwargs):
        response = self._client.request(method, url, **kwargs)
        return _RequestsCompatResponse(response)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request('PATCH', url, **kwargs)

    def head(self, url, **kwargs):
        return self.request('HEAD', url, **kwargs)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class _RequestsCompatModule:
    """
    Wraps httpx to provide requests-compatible module interface.
    """

    def __init__(self):
        self.exceptions = httpx.exceptions

    @property
    def Session(self):
        return _RequestsCompatSession

    def get(self, url, **kwargs):
        with httpx.Client() as client:
            response = client.get(url, **kwargs)
            return _RequestsCompatResponse(response)

    def post(self, url, **kwargs):
        with httpx.Client() as client:
            response = client.post(url, **kwargs)
            return _RequestsCompatResponse(response)

    def put(self, url, **kwargs):
        with httpx.Client() as client:
            response = client.put(url, **kwargs)
            return _RequestsCompatResponse(response)

    def delete(self, url, **kwargs):
        with httpx.Client() as client:
            response = client.delete(url, **kwargs)
            return _RequestsCompatResponse(response)

    def patch(self, url, **kwargs):
        with httpx.Client() as client:
            response = client.patch(url, **kwargs)
            return _RequestsCompatResponse(response)

    def head(self, url, **kwargs):
        with httpx.Client() as client:
            response = client.head(url, **kwargs)
            return _RequestsCompatResponse(response)

    def request(self, method, url, **kwargs):
        with httpx.Client() as client:
            response = client.request(method, url, **kwargs)
            return _RequestsCompatResponse(response)

    def Session(self):
        return _RequestsCompatSession()


# For 'from requests.packages import urllib3' compatibility
class _Urllib3Compat:
    exceptions = httpx.exceptions

    class exceptions:
        class InsecureRequestWarning(Warning):
            pass

        class InsecurePlatformWarning(Warning):
            pass

        class SNIMissingWarning(Warning):
            pass

    @staticmethod
    def disable_warnings():
        # httpx doesn't have equivalent, but we can at least provide the method
        pass


# Create module instances for compatibility
requests = _RequestsCompatModule()
urllib3 = _Urllib3Compat()
