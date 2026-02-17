"""API tests for Attribute dependency (depends_on) functionality."""

import pytest

pytestmark = pytest.mark.django_db

from rest_framework import status

from .util import assert_error, get_result


def test_create_with_depends_on(client, site):
    """Create an attribute with depends_on referencing another attribute."""
    attr_uri = site.list_uri("attribute")

    resp_b = client.create(attr_uri, resource_name="Device", name="b")
    assert resp_b.status_code == status.HTTP_201_CREATED

    resp_a = client.create(
        attr_uri, resource_name="Device", name="a", depends_on=["b"]
    )
    assert resp_a.status_code == status.HTTP_201_CREATED
    result = get_result(resp_a)
    assert result["depends_on"] == ["b"]


def test_read_shows_depends_on(client, site):
    """Read attribute shows depends_on as list of names."""
    attr_uri = site.list_uri("attribute")

    client.create(attr_uri, resource_name="Device", name="b")
    resp = client.create(
        attr_uri, resource_name="Device", name="a", depends_on=["b"]
    )
    attr = get_result(resp)

    obj_uri = site.detail_uri("attribute", id=attr["id"])
    result = get_result(client.get(obj_uri))
    assert result["depends_on"] == ["b"]


def test_update_depends_on(client, site):
    """Update attribute to add/remove dependencies."""
    attr_uri = site.list_uri("attribute")

    client.create(attr_uri, resource_name="Device", name="b")
    client.create(attr_uri, resource_name="Device", name="c")
    resp_a = client.create(attr_uri, resource_name="Device", name="a")
    attr_a = get_result(resp_a)
    obj_uri = site.detail_uri("attribute", id=attr_a["id"])

    # Add dependency
    update_resp = client.update(obj_uri, depends_on=["b"])
    result = get_result(update_resp)
    assert result["depends_on"] == ["b"]

    # Change dependency
    update_resp = client.update(obj_uri, depends_on=["c"])
    result = get_result(update_resp)
    assert result["depends_on"] == ["c"]

    # Remove all dependencies
    update_resp = client.update(obj_uri, depends_on=[])
    result = get_result(update_resp)
    assert result["depends_on"] == []


def test_filter_has_dependencies(client, site):
    """Filter by has_dependencies=true/false."""
    attr_uri = site.list_uri("attribute")

    client.create(attr_uri, resource_name="Device", name="b")
    client.create(attr_uri, resource_name="Device", name="a", depends_on=["b"])
    client.create(attr_uri, resource_name="Device", name="c")

    resp = client.get(attr_uri + "?has_dependencies=true")
    results = get_result(resp)
    names = [r["name"] for r in results]
    assert "a" in names
    assert "b" not in names
    assert "c" not in names

    resp = client.get(attr_uri + "?has_dependencies=false")
    results = get_result(resp)
    names = [r["name"] for r in results]
    assert "a" not in names
    assert "b" in names
    assert "c" in names


def test_create_invalid_dependency_wrong_resource(client, site):
    """Create with invalid dependency (wrong resource_name) returns error."""
    attr_uri = site.list_uri("attribute")

    client.create(attr_uri, resource_name="Network", name="net_attr")
    resp = client.create(
        attr_uri,
        resource_name="Device",
        name="dev_attr",
        depends_on=["net_attr"],
    )
    assert_error(resp, status.HTTP_400_BAD_REQUEST)


def test_delete_with_dependents_returns_error(client, site):
    """Delete attribute with dependents returns clear error."""
    attr_uri = site.list_uri("attribute")

    resp_b = client.create(attr_uri, resource_name="Device", name="b")
    attr_b = get_result(resp_b)
    client.create(attr_uri, resource_name="Device", name="a", depends_on=["b"])

    obj_uri = site.detail_uri("attribute", id=attr_b["id"])
    del_resp = client.delete(obj_uri)
    assert_error(del_resp, status.HTTP_400_BAD_REQUEST)
