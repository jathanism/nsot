"""Tests for bulk delete support."""

import json

import pytest
from rest_framework import status

from .util import assert_deleted, assert_error, get_result

pytestmark = pytest.mark.django_db


def bulk_delete(client, url, ids):
    """Send a DELETE request with a JSON body of IDs.

    The test Client doesn't set Content-Type for DELETE, so we use the
    session directly.
    """
    headers = {
        "X-NSoT-Email": client.user,
        "Content-type": "application/json",
    }
    return client.session.request(
        "DELETE",
        client.base_url + url,
        headers=headers,
        data=json.dumps(ids),
    )


def test_bulk_delete_devices(client, site):
    """Test bulk deletion of multiple devices."""
    dev_uri = site.list_uri("device")

    dev1 = get_result(client.create(dev_uri, hostname="device1"))
    dev2 = get_result(client.create(dev_uri, hostname="device2"))
    dev3 = get_result(client.create(dev_uri, hostname="device3"))

    resp = bulk_delete(client, dev_uri, [dev1["id"], dev2["id"]])
    assert_deleted(resp)

    remaining = get_result(client.get(dev_uri))
    assert len(remaining) == 1
    assert remaining[0]["hostname"] == "device3"


def test_bulk_delete_empty_list(client, site):
    """Test bulk delete with empty list returns 400."""
    dev_uri = site.list_uri("device")
    resp = bulk_delete(client, dev_uri, [])
    assert_error(resp, status.HTTP_400_BAD_REQUEST)


def test_bulk_delete_nonexistent_id(client, site):
    """Test bulk delete with non-existent ID returns 404."""
    dev_uri = site.list_uri("device")
    resp = bulk_delete(client, dev_uri, [99999])
    assert_error(resp, status.HTTP_404_NOT_FOUND)


def test_bulk_delete_invalid_payload(client, site):
    """Test bulk delete with non-list payload returns 400."""
    dev_uri = site.list_uri("device")
    resp = bulk_delete(client, dev_uri, {"ids": [1]})
    assert_error(resp, status.HTTP_400_BAD_REQUEST)


def test_bulk_delete_invalid_id_type(client, site):
    """Test bulk delete with non-integer IDs returns 400."""
    dev_uri = site.list_uri("device")
    resp = bulk_delete(client, dev_uri, ["abc"])
    assert_error(resp, status.HTTP_400_BAD_REQUEST)


def test_bulk_delete_permissions(client, user_client, user, site):
    """Test that non-admin users cannot bulk delete."""
    dev_uri = site.list_uri("device")
    dev1 = get_result(client.create(dev_uri, hostname="device1"))

    resp = bulk_delete(user_client, dev_uri, [dev1["id"]])
    assert_error(resp, status.HTTP_403_FORBIDDEN)


def test_bulk_delete_networks(client, site):
    """Test bulk deletion of networks."""
    net_uri = site.list_uri("network")

    net1 = get_result(client.create(net_uri, cidr="10.0.0.0/8"))
    net2 = get_result(client.create(net_uri, cidr="192.168.0.0/16"))

    resp = bulk_delete(client, net_uri, [net1["id"], net2["id"]])
    assert_deleted(resp)

    remaining = get_result(client.get(net_uri))
    assert len(remaining) == 0


def test_bulk_delete_attributes(client, site):
    """Test bulk deletion of attributes."""
    attr_uri = site.list_uri("attribute")

    attr1 = get_result(
        client.create(attr_uri, resource_name="Device", name="attr1")
    )
    attr2 = get_result(
        client.create(attr_uri, resource_name="Device", name="attr2")
    )

    resp = bulk_delete(client, attr_uri, [attr1["id"], attr2["id"]])
    assert_deleted(resp)

    remaining = get_result(client.get(attr_uri))
    assert len(remaining) == 0
