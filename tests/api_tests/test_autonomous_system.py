import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import logging

from rest_framework import status

from .util import (
    assert_created,
    assert_deleted,
    assert_error,
    assert_success,
    get_result,
)

log = logging.getLogger(__name__)


def test_creation(client, site):
    """Test creation of AutonomousSystems."""
    attr_uri = site.list_uri("attribute")
    asn_uri = site.list_uri("autonomoussystem")

    client.create(attr_uri, resource_name="AutonomousSystem", name="owner")

    # Create with attributes
    resp = client.create(
        asn_uri,
        number=65001,
        description="Test ASN",
        attributes={"owner": "jathan"},
    )
    asn = get_result(resp)
    asn_obj_uri = site.detail_uri("autonomoussystem", id=asn["id"])
    assert_created(resp, asn_obj_uri)
    assert asn["number"] == 65001
    assert asn["description"] == "Test ASN"
    assert asn["attributes"] == {"owner": "jathan"}
    assert asn["number_asdot"] == "65001"

    # Verify list
    assert_success(client.get(asn_uri), [asn])

    # Verify retrieve
    assert_success(client.get(asn_obj_uri), asn)


def test_natural_key_lookup(client, site):
    """Test natural key lookup by ASN number."""
    asn_uri = site.list_uri("autonomoussystem")
    resp = client.create(asn_uri, number=65001)
    asn = get_result(resp)

    natural_uri = site.detail_uri("autonomoussystem", id=65001)
    assert_success(client.get(natural_uri), asn)


def test_number_asdot_in_response(client, site):
    """Test that number_asdot is in the response for 32-bit ASNs."""
    asn_uri = site.list_uri("autonomoussystem")
    resp = client.create(asn_uri, number=65536)
    asn = get_result(resp)
    assert asn["number_asdot"] == "1.0"


def test_unique_constraint(client, site):
    """Test unique constraint via API returns 400/409."""
    asn_uri = site.list_uri("autonomoussystem")
    client.create(asn_uri, number=65001)
    resp = client.create(asn_uri, number=65001)
    assert resp.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
    )


def test_validation_invalid_range(client, site):
    """Test validation via API for invalid ASN range."""
    asn_uri = site.list_uri("autonomoussystem")

    assert_error(
        client.create(asn_uri, number=0),
        status.HTTP_400_BAD_REQUEST,
    )
    assert_error(
        client.create(asn_uri, number=4294967295),
        status.HTTP_400_BAD_REQUEST,
    )


def test_update_put(client, site):
    """Test PUT update of an AutonomousSystem."""
    attr_uri = site.list_uri("attribute")
    asn_uri = site.list_uri("autonomoussystem")

    client.create(attr_uri, resource_name="AutonomousSystem", name="owner")

    resp = client.create(asn_uri, number=65001, attributes={"owner": "jathan"})
    asn = get_result(resp)
    asn_obj_uri = site.detail_uri("autonomoussystem", id=asn["id"])

    # PUT requires attributes
    params = {
        "number": 65002,
        "description": "Updated",
        "attributes": {"owner": "gary"},
    }
    asn.update(params)
    asn["number_asdot"] = "65002"  # Update expected asdot to match new number
    assert_success(client.update(asn_obj_uri, **params), asn)


def test_partial_update_patch(client, site):
    """Test PATCH partial update of an AutonomousSystem."""
    asn_uri = site.list_uri("autonomoussystem")
    resp = client.create(asn_uri, number=65001, description="Original")
    asn = get_result(resp)
    asn_obj_uri = site.detail_uri("autonomoussystem", id=asn["id"])

    params = {"description": "Patched"}
    asn.update(params)
    assert_success(client.partial_update(asn_obj_uri, **params), asn)


def test_deletion(client, site):
    """Test deletion of an AutonomousSystem."""
    asn_uri = site.list_uri("autonomoussystem")
    resp = client.create(asn_uri, number=65001)
    asn = get_result(resp)
    asn_obj_uri = site.detail_uri("autonomoussystem", id=asn["id"])
    assert_deleted(client.delete(asn_obj_uri))


def test_filter_by_number(client, site):
    """Test filtering by number."""
    asn_uri = site.list_uri("autonomoussystem")
    client.create(asn_uri, number=65001)
    client.create(asn_uri, number=65002)

    resp = client.retrieve(asn_uri, number=65001)
    results = get_result(resp)
    assert len(results) == 1
    assert results[0]["number"] == 65001


def test_filter_by_description(client, site):
    """Test filtering by description."""
    asn_uri = site.list_uri("autonomoussystem")
    client.create(asn_uri, number=65001, description="Provider A")
    client.create(asn_uri, number=65002, description="Provider B")

    resp = client.retrieve(asn_uri, description="Provider A")
    results = get_result(resp)
    assert len(results) == 1
    assert results[0]["number"] == 65001


def test_filter_by_attributes(client, site):
    """Test filtering by attributes."""
    attr_uri = site.list_uri("attribute")
    asn_uri = site.list_uri("autonomoussystem")

    client.create(attr_uri, resource_name="AutonomousSystem", name="region")

    client.create(asn_uri, number=65001, attributes={"region": "us-west"})
    client.create(asn_uri, number=65002, attributes={"region": "us-east"})

    resp = client.retrieve(asn_uri, attributes="region=us-west")
    results = get_result(resp)
    assert len(results) == 1
    assert results[0]["number"] == 65001


def test_expires_at(client, site):
    """Test expires_at support."""
    asn_uri = site.list_uri("autonomoussystem")
    resp = client.create(
        asn_uri, number=65001, expires_at="2099-12-31T23:59:59Z"
    )
    asn = get_result(resp)
    assert asn["expires_at"] is not None


def test_protocol_fk(client, site):
    """Test Protocol FK to AutonomousSystem."""
    asn_uri = site.list_uri("autonomoussystem")
    dev_uri = site.list_uri("device")
    pt_uri = site.list_uri("protocoltype")
    proto_uri = site.list_uri("protocol")

    # Create AS
    asn_resp = client.create(asn_uri, number=65001)
    asn = get_result(asn_resp)

    # Create device
    dev_resp = client.create(dev_uri, hostname="router1")
    dev = get_result(dev_resp)

    # Create protocol type
    pt_resp = client.create(pt_uri, name="bgp", description="BGP")
    pt = get_result(pt_resp)

    # Create protocol with autonomous_system
    proto_resp = client.create(
        proto_uri,
        device=dev["id"],
        type=pt["name"],
        autonomous_system=asn["id"],
    )
    proto = get_result(proto_resp)
    assert proto["autonomous_system"] == asn["id"]
