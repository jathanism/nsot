"""
Tests for drf-flex-fields query parameters: ?expand, ?fields, ?omit.
"""

import pytest

pytestmark = pytest.mark.django_db

import logging

from .util import get_result

log = logging.getLogger(__name__)


def _create_device(client, site_uri, hostname="foo-bar1"):
    """Helper to create a device and return its data."""
    resp = client.create(site_uri, hostname=hostname)
    assert resp.status_code == 201, resp.json()
    return get_result(resp)


def _create_interface(client, site_uri, device_id, name="eth0"):
    """Helper to create an interface and return its data."""
    resp = client.create(site_uri, device=device_id, name=name)
    assert resp.status_code == 201, resp.json()
    return get_result(resp)


class TestFieldsParam:
    """Test ?fields=field1,field2 for sparse fieldsets."""

    def test_fields_returns_only_specified(self, client, site):
        """?fields=id,hostname returns only those two fields."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"fields": "id,hostname"})
        assert resp.status_code == 200
        results = get_result(resp)
        assert len(results) == 1
        device = results[0]
        assert set(device.keys()) == {"id", "hostname"}

    def test_fields_single_field(self, client, site):
        """?fields=id returns only id."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"fields": "id"})
        assert resp.status_code == 200
        results = get_result(resp)
        device = results[0]
        assert set(device.keys()) == {"id"}


class TestOmitParam:
    """Test ?omit=field1,field2 for excluding fields."""

    def test_omit_removes_field(self, client, site):
        """?omit=attributes removes the attributes key."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"omit": "attributes"})
        assert resp.status_code == 200
        results = get_result(resp)
        device = results[0]
        assert "attributes" not in device
        # Other fields still present
        assert "id" in device
        assert "hostname" in device

    def test_omit_multiple_fields(self, client, site):
        """?omit=attributes,hostname removes both."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"omit": "attributes,hostname"})
        assert resp.status_code == 200
        results = get_result(resp)
        device = results[0]
        assert "attributes" not in device
        assert "hostname" not in device
        assert "id" in device


class TestExpandParam:
    """Test ?expand=field for nested object expansion."""

    def test_expand_site_on_device(self, client, site):
        """?expand=site_id on devices returns nested site object."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"expand": "site_id"})
        assert resp.status_code == 200
        results = get_result(resp)
        device = results[0]
        # site_id should now be a dict (nested site object)
        assert isinstance(device["site_id"], dict)
        assert "name" in device["site_id"]

    def test_expand_device_on_interface(self, client, site):
        """?expand=device on interfaces returns nested device object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        device = _create_device(client, dev_uri)

        _create_interface(client, iface_uri, device["id"])

        resp = client.get(iface_uri, params={"expand": "device"})
        assert resp.status_code == 200
        results = get_result(resp)
        iface = results[0]
        # device should now be a nested dict
        assert isinstance(iface["device"], dict)
        assert "hostname" in iface["device"]
        assert iface["device"]["hostname"] == "foo-bar1"

    def test_invalid_expand_ignored(self, client, site):
        """?expand=nonexistent is silently ignored."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"expand": "nonexistent"})
        assert resp.status_code == 200
        results = get_result(resp)
        device = results[0]
        # Should still be a normal response
        assert "id" in device
        assert "hostname" in device


class TestDefaultResponse:
    """Verify default responses (no flex params) are unchanged."""

    def test_default_device_response(self, client, site):
        """No query params returns standard flat response."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri)
        assert resp.status_code == 200
        results = get_result(resp)
        device = results[0]
        # site_id should be an integer, not a nested object
        assert isinstance(device["site_id"], int)
        assert "hostname" in device
        assert "attributes" in device

    def test_default_interface_response(self, client, site):
        """No query params returns standard flat response for interfaces."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        device = _create_device(client, dev_uri)
        _create_interface(client, iface_uri, device["id"])

        resp = client.get(iface_uri)
        assert resp.status_code == 200
        results = get_result(resp)
        iface = results[0]
        # device should be a hostname string (NaturalKeyRelatedField)
        assert isinstance(iface["device"], str)
