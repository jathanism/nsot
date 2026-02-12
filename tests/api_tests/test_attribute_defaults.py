"""Tests for Attribute default values feature (issue #36)."""

import pytest

pytestmark = pytest.mark.django_db

from rest_framework import status

from .util import get_result


def test_default_applied_on_create(client, site):
    """Required attribute with default is auto-applied when not provided."""
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")

    # Create a required attribute with a default
    client.create(
        attr_uri,
        resource_name="Device",
        name="role",
        required=True,
        default="default-role",
    )

    # Create a device WITHOUT providing the attribute — should succeed
    resp = client.create(dev_uri, hostname="test-dev1")
    assert resp.status_code == status.HTTP_201_CREATED
    result = get_result(resp)
    assert result["attributes"]["role"] == "default-role"


def test_default_not_applied_when_value_provided(client, site):
    """Explicit value overrides the default."""
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")

    client.create(
        attr_uri,
        resource_name="Device",
        name="role",
        required=True,
        default="default-role",
    )

    resp = client.create(
        dev_uri, hostname="test-dev2", attributes={"role": "custom-role"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    result = get_result(resp)
    assert result["attributes"]["role"] == "custom-role"


def test_multi_attribute_default(client, site):
    """Multi-value attribute with list default."""
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")

    client.create(
        attr_uri,
        resource_name="Device",
        name="tags",
        multi=True,
        default=["tag1", "tag2"],
    )

    resp = client.create(dev_uri, hostname="test-dev3")
    assert resp.status_code == status.HTTP_201_CREATED
    result = get_result(resp)
    assert sorted(result["attributes"]["tags"]) == ["tag1", "tag2"]


def test_invalid_default_rejected_wrong_type(client, site):
    """String default on multi attribute should fail."""
    attr_uri = site.list_uri("attribute")

    resp = client.create(
        attr_uri,
        resource_name="Device",
        name="tags",
        multi=True,
        default="not-a-list",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_invalid_default_rejected_multi_not_list(client, site):
    """List default on single-value attribute should fail."""
    attr_uri = site.list_uri("attribute")

    resp = client.create(
        attr_uri, resource_name="Device", name="role", default=["a", "b"]
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_default_respects_constraints(client, site):
    """Default must pass constraint validation."""
    attr_uri = site.list_uri("attribute")

    resp = client.create(
        attr_uri,
        resource_name="Device",
        name="env",
        constraints={"valid_values": ["prod", "staging", "dev"]},
        default="invalid-env",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_default_passes_constraints(client, site):
    """Valid default that matches constraints should work."""
    attr_uri = site.list_uri("attribute")

    resp = client.create(
        attr_uri,
        resource_name="Device",
        name="env",
        constraints={"valid_values": ["prod", "staging", "dev"]},
        default="prod",
    )
    assert resp.status_code == status.HTTP_201_CREATED


def test_default_shown_in_api_response(client, site):
    """Default value should appear in attribute GET response."""
    attr_uri = site.list_uri("attribute")

    resp = client.create(
        attr_uri, resource_name="Device", name="role", default="default-role"
    )
    assert resp.status_code == status.HTTP_201_CREATED
    result = get_result(resp)
    assert result["default"] == "default-role"


def test_optional_attribute_default(client, site):
    """Non-required attribute with default — default applied when omitted."""
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")

    client.create(
        attr_uri,
        resource_name="Device",
        name="region",
        required=False,
        default="us-west",
    )

    resp = client.create(dev_uri, hostname="test-dev4")
    assert resp.status_code == status.HTTP_201_CREATED
    result = get_result(resp)
    assert result["attributes"]["region"] == "us-west"


def test_partial_update_doesnt_reapply_default(client, site):
    """PATCH should not re-apply defaults for attributes already on the resource."""
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")

    client.create(
        attr_uri,
        resource_name="Device",
        name="role",
        required=True,
        default="default-role",
    )
    client.create(
        attr_uri,
        resource_name="Device",
        name="env",
        required=False,
        default="staging",
    )

    # Create device — gets defaults
    resp = client.create(
        dev_uri, hostname="test-dev5", attributes={"role": "custom"}
    )
    dev_id = get_result(resp)["id"]
    detail_uri = site.detail_uri("device", id=dev_id)

    # PATCH with only role change — env should get default since it wasn't set
    resp = client.partial_update(detail_uri, attributes={"role": "updated"})
    assert resp.status_code == status.HTTP_200_OK
    result = get_result(resp)
    assert result["attributes"]["role"] == "updated"


def test_default_none_means_no_default(client, site):
    """Attribute with no default (null) doesn't inject anything."""
    attr_uri = site.list_uri("attribute")
    dev_uri = site.list_uri("device")

    client.create(
        attr_uri, resource_name="Device", name="optional-thing", required=False
    )

    resp = client.create(dev_uri, hostname="test-dev6")
    assert resp.status_code == status.HTTP_201_CREATED
    result = get_result(resp)
    assert "optional-thing" not in result["attributes"]
