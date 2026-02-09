import logging

import pytest

# Allow everything in here to access the DB
pytestmark = pytest.mark.django_db

import requests

from .util import assert_success

log = logging.getLogger(__name__)


def test_request_xforwardfor(live_server):
    """Test processing of X-Forwarded-For header."""
    url = f"{live_server.url}/api/sites/"
    headers = {"X-NSoT-Email": "gary@localhost", "X-Forward-For": "10.1.1.1"}

    expected = []

    assert_success(requests.get(url, headers=headers), expected)
