"""Tests for attribute inheritance on hierarchical resources."""

import pytest

pytestmark = pytest.mark.django_db

import logging

from rest_framework import status

from .util import Client, get_result

log = logging.getLogger(__name__)


def test_basic_inheritance(live_server, site):
    """Root network has inheritable attr; child inherits via ?include_inherited=true."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    # Create inheritable attribute
    resp = client.create(
        attr_uri, resource_name="Network", name="region", inheritable=True
    )
    assert resp.status_code == status.HTTP_201_CREATED

    # Create root network with attribute
    resp = client.create(
        net_uri, cidr="10.0.0.0/8", attributes={"region": "us-west"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    root = get_result(resp)

    # Create child network (no explicit attribute)
    resp = client.create(net_uri, cidr="10.1.0.0/16")
    assert resp.status_code == status.HTTP_201_CREATED
    child = get_result(resp)

    # Fetch child with include_inherited
    resp = client.retrieve(
        site.detail_uri("network", id=child["id"]),
        include_inherited="true",
    )
    assert resp.status_code == status.HTTP_200_OK
    result = get_result(resp)

    merged = result["merged_attributes"]
    assert merged is not None
    assert merged["region"]["value"] == "us-west"
    assert merged["region"]["inherited"] is True
    assert merged["region"]["source"] == "10.0.0.0/8"


def test_override(live_server, site):
    """Child's explicit value wins over parent's inherited value."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    client.create(
        attr_uri, resource_name="Network", name="region", inheritable=True
    )

    client.create(net_uri, cidr="10.0.0.0/8", attributes={"region": "us-west"})
    resp = client.create(
        net_uri, cidr="10.1.0.0/16", attributes={"region": "us-east"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    child = get_result(resp)

    resp = client.retrieve(
        site.detail_uri("network", id=child["id"]),
        include_inherited="true",
    )
    result = get_result(resp)
    merged = result["merged_attributes"]
    assert merged["region"]["value"] == "us-east"
    assert merged["region"]["inherited"] is False
    assert merged["region"]["source"] == "self"


def test_multi_level_inheritance(live_server, site):
    """Root → mid → leaf; mid doesn't set attr, leaf inherits from root."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    client.create(
        attr_uri, resource_name="Network", name="region", inheritable=True
    )
    client.create(net_uri, cidr="10.0.0.0/8", attributes={"region": "us-west"})
    client.create(net_uri, cidr="10.1.0.0/16")
    resp = client.create(net_uri, cidr="10.1.1.0/24")
    assert resp.status_code == status.HTTP_201_CREATED
    leaf = get_result(resp)

    resp = client.retrieve(
        site.detail_uri("network", id=leaf["id"]),
        include_inherited="true",
    )
    result = get_result(resp)
    merged = result["merged_attributes"]
    assert merged["region"]["value"] == "us-west"
    assert merged["region"]["inherited"] is True
    assert merged["region"]["source"] == "10.0.0.0/8"


def test_non_inheritable_does_not_propagate(live_server, site):
    """inheritable=False attribute never propagates to children."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    client.create(
        attr_uri, resource_name="Network", name="owner", inheritable=False
    )
    client.create(net_uri, cidr="10.0.0.0/8", attributes={"owner": "jathan"})
    resp = client.create(net_uri, cidr="10.1.0.0/16")
    child = get_result(resp)

    resp = client.retrieve(
        site.detail_uri("network", id=child["id"]),
        include_inherited="true",
    )
    result = get_result(resp)
    merged = result["merged_attributes"]
    assert "owner" not in merged


def test_filter_expansion(live_server, site):
    """?attributes=region=us-west returns root + inheriting children."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    client.create(
        attr_uri, resource_name="Network", name="region", inheritable=True
    )
    client.create(net_uri, cidr="10.0.0.0/8", attributes={"region": "us-west"})
    client.create(net_uri, cidr="10.1.0.0/16")
    client.create(net_uri, cidr="10.1.1.0/24")

    resp = client.retrieve(net_uri, attributes="region=us-west")
    assert resp.status_code == status.HTTP_200_OK
    results = get_result(resp)
    cidrs = {
        r["network_address"] + "/" + str(r["prefix_length"]) for r in results
    }
    assert "10.0.0.0/8" in cidrs
    assert "10.1.0.0/16" in cidrs
    assert "10.1.1.0/24" in cidrs


def test_filter_with_override_excluded(live_server, site):
    """Child with different explicit value is excluded from filter expansion."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    client.create(
        attr_uri, resource_name="Network", name="region", inheritable=True
    )
    client.create(net_uri, cidr="10.0.0.0/8", attributes={"region": "us-west"})
    client.create(
        net_uri, cidr="10.1.0.0/16", attributes={"region": "us-east"}
    )
    client.create(net_uri, cidr="10.2.0.0/16")  # inherits us-west

    resp = client.retrieve(net_uri, attributes="region=us-west")
    results = get_result(resp)
    cidrs = {
        r["network_address"] + "/" + str(r["prefix_length"]) for r in results
    }
    assert "10.0.0.0/8" in cidrs
    assert "10.1.0.0/16" not in cidrs
    assert "10.2.0.0/16" in cidrs


def test_interface_inheritance(live_server, site):
    """Interface inherits attributes from parent interface."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")
    iface_uri = site.list_uri("interface")

    client.create(
        attr_uri,
        resource_name="Interface",
        name="speed_class",
        inheritable=True,
    )
    resp = client.create(dev_uri, hostname="router1")
    assert resp.status_code == status.HTTP_201_CREATED

    # Create parent interface
    resp = client.create(
        iface_uri,
        device="router1",
        name="eth0",
        attributes={"speed_class": "10g"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    parent = get_result(resp)

    # Create child interface
    resp = client.create(
        iface_uri,
        device="router1",
        name="eth0.1",
        parent_id=parent["id"],
    )
    assert resp.status_code == status.HTTP_201_CREATED
    child = get_result(resp)

    resp = client.retrieve(
        site.detail_uri("interface", id=child["id"]),
        include_inherited="true",
    )
    result = get_result(resp)
    merged = result["merged_attributes"]
    assert merged["speed_class"]["value"] == "10g"
    assert merged["speed_class"]["inherited"] is True


def test_invalid_resource_type(live_server, site):
    """inheritable=True on Device attr raises validation error."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")

    resp = client.create(
        attr_uri, resource_name="Device", name="region", inheritable=True
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_without_include_inherited(live_server, site):
    """Without ?include_inherited, merged_attributes is null."""
    client = Client(live_server)
    attr_uri = site.list_uri("attribute")
    net_uri = site.list_uri("network")

    client.create(
        attr_uri, resource_name="Network", name="region", inheritable=True
    )
    resp = client.create(
        net_uri, cidr="10.0.0.0/8", attributes={"region": "us-west"}
    )
    net = get_result(resp)

    resp = client.retrieve(site.detail_uri("network", id=net["id"]))
    result = get_result(resp)
    assert result["merged_attributes"] is None
