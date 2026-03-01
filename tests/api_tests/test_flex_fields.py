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


class TestExpandAllModels:
    """Comprehensive expand tests for every expandable_field on every serializer."""

    # -- Attribute --
    def test_expand_site_on_attribute(self, client, site):
        """?expand=site_id on attributes returns nested site object."""
        attr_uri = site.list_uri("attribute")
        resp = client.create(
            attr_uri, name="test_attr", resource_name="Device"
        )
        assert resp.status_code == 201

        resp = client.get(attr_uri, params={"expand": "site_id"})
        assert resp.status_code == 200
        results = get_result(resp)
        attr = results[0]
        assert isinstance(attr["site_id"], dict)
        assert "name" in attr["site_id"]

    # -- Device --
    def test_expand_site_on_device(self, client, site):
        """?expand=site_id on devices returns nested site object."""
        dev_uri = site.list_uri("device")
        _create_device(client, dev_uri)

        resp = client.get(dev_uri, params={"expand": "site_id"})
        assert resp.status_code == 200
        device = get_result(resp)[0]
        assert isinstance(device["site_id"], dict)
        assert "name" in device["site_id"]

    # -- Network --
    def test_expand_site_on_network(self, client, site):
        """?expand=site_id on networks returns nested site object."""
        net_uri = site.list_uri("network")
        resp = client.create(net_uri, cidr="10.0.0.0/8")
        assert resp.status_code == 201

        resp = client.get(net_uri, params={"expand": "site_id"})
        assert resp.status_code == 200
        net = get_result(resp)[0]
        assert isinstance(net["site_id"], dict)
        assert "name" in net["site_id"]

    def test_expand_parent_on_network(self, client, site):
        """?expand=parent_id on networks returns nested parent network."""
        net_uri = site.list_uri("network")
        resp = client.create(net_uri, cidr="10.0.0.0/8")
        assert resp.status_code == 201
        resp = client.create(net_uri, cidr="10.0.0.0/24")
        assert resp.status_code == 201
        child = get_result(resp)

        detail_uri = site.detail_uri("network", id=child["id"])
        resp = client.get(detail_uri, params={"expand": "parent_id"})
        assert resp.status_code == 200
        net = get_result(resp)
        assert isinstance(net["parent_id"], dict)
        assert "cidr" in net["parent_id"]
        assert net["parent_id"]["cidr"] == "10.0.0.0/8"

    def test_expand_multiple_on_network(self, client, site):
        """?expand=site_id,parent_id on networks expands both fields."""
        net_uri = site.list_uri("network")
        client.create(net_uri, cidr="10.0.0.0/8")
        resp = client.create(net_uri, cidr="10.0.0.0/24")
        assert resp.status_code == 201
        child = get_result(resp)

        detail_uri = site.detail_uri("network", id=child["id"])
        resp = client.get(detail_uri, params={"expand": "site_id,parent_id"})
        assert resp.status_code == 200
        net = get_result(resp)
        assert isinstance(net["site_id"], dict)
        assert isinstance(net["parent_id"], dict)

    # -- Interface --
    def test_expand_device_on_interface(self, client, site):
        """?expand=device on interfaces returns nested device object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        device = _create_device(client, dev_uri)
        _create_interface(client, iface_uri, device["id"])

        resp = client.get(iface_uri, params={"expand": "device"})
        assert resp.status_code == 200
        iface = get_result(resp)[0]
        assert isinstance(iface["device"], dict)
        assert "hostname" in iface["device"]

    def test_expand_parent_on_interface(self, client, site):
        """?expand=parent_id on interfaces returns nested parent interface."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        device = _create_device(client, dev_uri)
        parent = _create_interface(
            client, iface_uri, device["id"], name="eth0"
        )
        resp = client.create(
            iface_uri,
            device=device["id"],
            name="eth0.1",
            parent_id=parent["id"],
        )
        assert resp.status_code == 201
        child = get_result(resp)

        detail_uri = site.detail_uri("interface", id=child["id"])
        resp = client.get(detail_uri, params={"expand": "parent_id"})
        assert resp.status_code == 200
        iface = get_result(resp)
        assert isinstance(iface["parent_id"], dict)
        assert "name" in iface["parent_id"]
        assert iface["parent_id"]["name"] == "eth0"

    # -- Circuit --
    def test_expand_site_on_circuit(self, client, site):
        """?expand=site_id on circuits returns nested site object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        circuit_uri = site.list_uri("circuit")
        device = _create_device(client, dev_uri)
        iface_a = _create_interface(
            client, iface_uri, device["id"], name="eth0"
        )
        iface_z = _create_interface(
            client, iface_uri, device["id"], name="eth1"
        )
        resp = client.create(
            circuit_uri,
            endpoint_a=iface_a["id"],
            endpoint_z=iface_z["id"],
            name="test-circuit",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(circuit_uri, params={"expand": "site_id"})
        assert resp.status_code == 200
        circuit = get_result(resp)[0]
        assert isinstance(circuit["site_id"], dict)
        assert "name" in circuit["site_id"]

    def test_expand_endpoint_a_on_circuit(self, client, site):
        """?expand=endpoint_a on circuits returns nested interface object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        circuit_uri = site.list_uri("circuit")
        device = _create_device(client, dev_uri)
        iface_a = _create_interface(
            client, iface_uri, device["id"], name="eth0"
        )
        iface_z = _create_interface(
            client, iface_uri, device["id"], name="eth1"
        )
        resp = client.create(
            circuit_uri,
            endpoint_a=iface_a["id"],
            endpoint_z=iface_z["id"],
            name="test-circuit",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(circuit_uri, params={"expand": "endpoint_a"})
        assert resp.status_code == 200
        circuit = get_result(resp)[0]
        assert isinstance(circuit["endpoint_a"], dict)
        assert "name" in circuit["endpoint_a"]
        assert circuit["endpoint_a"]["name"] == "eth0"

    def test_expand_endpoint_z_on_circuit(self, client, site):
        """?expand=endpoint_z on circuits returns nested interface object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        circuit_uri = site.list_uri("circuit")
        device = _create_device(client, dev_uri)
        iface_a = _create_interface(
            client, iface_uri, device["id"], name="eth0"
        )
        iface_z = _create_interface(
            client, iface_uri, device["id"], name="eth1"
        )
        resp = client.create(
            circuit_uri,
            endpoint_a=iface_a["id"],
            endpoint_z=iface_z["id"],
            name="test-circuit",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(circuit_uri, params={"expand": "endpoint_z"})
        assert resp.status_code == 200
        circuit = get_result(resp)[0]
        assert isinstance(circuit["endpoint_z"], dict)
        assert "name" in circuit["endpoint_z"]
        assert circuit["endpoint_z"]["name"] == "eth1"

    # -- ProtocolType --
    def test_expand_site_on_protocol_type(self, client, site):
        """?expand=site on protocol_types returns nested site object."""
        pt_uri = site.list_uri("protocoltype")
        resp = client.create(pt_uri, name="bgp", description="BGP protocol")
        assert resp.status_code == 201, resp.json()

        resp = client.get(pt_uri, params={"expand": "site"})
        assert resp.status_code == 200
        pt = get_result(resp)[0]
        assert isinstance(pt["site"], dict)
        assert "name" in pt["site"]

    # -- Protocol --
    def test_expand_site_on_protocol(self, client, site):
        """?expand=site on protocols returns nested site object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        pt_uri = site.list_uri("protocoltype")
        proto_uri = site.list_uri("protocol")

        device = _create_device(client, dev_uri)
        iface = _create_interface(client, iface_uri, device["id"])
        pt_resp = client.create(pt_uri, name="bgp", description="BGP protocol")
        assert pt_resp.status_code == 201, pt_resp.json()

        resp = client.create(
            proto_uri,
            type="bgp",
            device=device["hostname"],
            interface=iface["name_slug"],
            description="test protocol",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(proto_uri, params={"expand": "site"})
        assert resp.status_code == 200
        proto = get_result(resp)[0]
        assert isinstance(proto["site"], dict)
        assert "name" in proto["site"]

    def test_expand_type_on_protocol(self, client, site):
        """?expand=type on protocols returns nested protocol type object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        pt_uri = site.list_uri("protocoltype")
        proto_uri = site.list_uri("protocol")

        device = _create_device(client, dev_uri)
        iface = _create_interface(client, iface_uri, device["id"])
        client.create(pt_uri, name="bgp", description="BGP protocol")

        resp = client.create(
            proto_uri,
            type="bgp",
            device=device["hostname"],
            interface=iface["name_slug"],
            description="test protocol",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(proto_uri, params={"expand": "type"})
        assert resp.status_code == 200
        proto = get_result(resp)[0]
        assert isinstance(proto["type"], dict)
        assert "name" in proto["type"]
        assert proto["type"]["name"] == "bgp"

    def test_expand_device_on_protocol(self, client, site):
        """?expand=device on protocols returns nested device object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        pt_uri = site.list_uri("protocoltype")
        proto_uri = site.list_uri("protocol")

        device = _create_device(client, dev_uri)
        iface = _create_interface(client, iface_uri, device["id"])
        client.create(pt_uri, name="bgp", description="BGP protocol")

        resp = client.create(
            proto_uri,
            type="bgp",
            device=device["hostname"],
            interface=iface["name_slug"],
            description="test protocol",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(proto_uri, params={"expand": "device"})
        assert resp.status_code == 200
        proto = get_result(resp)[0]
        assert isinstance(proto["device"], dict)
        assert "hostname" in proto["device"]
        assert proto["device"]["hostname"] == "foo-bar1"

    def test_expand_interface_on_protocol(self, client, site):
        """?expand=interface on protocols returns nested interface object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        pt_uri = site.list_uri("protocoltype")
        proto_uri = site.list_uri("protocol")

        device = _create_device(client, dev_uri)
        iface = _create_interface(client, iface_uri, device["id"])
        client.create(pt_uri, name="bgp", description="BGP protocol")

        resp = client.create(
            proto_uri,
            type="bgp",
            device=device["hostname"],
            interface=iface["name_slug"],
            description="test protocol",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(proto_uri, params={"expand": "interface"})
        assert resp.status_code == 200
        proto = get_result(resp)[0]
        assert isinstance(proto["interface"], dict)
        assert "name" in proto["interface"]

    def test_expand_circuit_on_protocol(self, client, site):
        """?expand=circuit on protocols returns nested circuit object."""
        dev_uri = site.list_uri("device")
        iface_uri = site.list_uri("interface")
        circuit_uri = site.list_uri("circuit")
        pt_uri = site.list_uri("protocoltype")
        proto_uri = site.list_uri("protocol")

        device = _create_device(client, dev_uri)
        iface_a = _create_interface(
            client, iface_uri, device["id"], name="eth0"
        )
        iface_z = _create_interface(
            client, iface_uri, device["id"], name="eth1"
        )
        iface_proto = _create_interface(
            client, iface_uri, device["id"], name="eth2"
        )
        resp = client.create(
            circuit_uri,
            endpoint_a=iface_a["id"],
            endpoint_z=iface_z["id"],
            name="test-circuit",
        )
        assert resp.status_code == 201, resp.json()

        client.create(pt_uri, name="bgp", description="BGP protocol")
        circuit = get_result(resp)

        resp = client.create(
            proto_uri,
            type="bgp",
            device=device["hostname"],
            interface=iface_proto["name_slug"],
            circuit=circuit["name_slug"],
            description="test protocol",
        )
        assert resp.status_code == 201, resp.json()

        resp = client.get(proto_uri, params={"expand": "circuit"})
        assert resp.status_code == 200
        proto = get_result(resp)[0]
        assert isinstance(proto["circuit"], dict)
        assert "name" in proto["circuit"]

    # -- Detail endpoint expansion --
    def test_expand_on_detail_endpoint(self, client, site):
        """?expand works on detail (retrieve) endpoints too."""
        dev_uri = site.list_uri("device")
        device = _create_device(client, dev_uri)

        detail_uri = site.detail_uri("device", id=device["id"])
        resp = client.get(detail_uri, params={"expand": "site_id"})
        assert resp.status_code == 200
        device = get_result(resp)
        assert isinstance(device["site_id"], dict)
        assert "name" in device["site_id"]


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
