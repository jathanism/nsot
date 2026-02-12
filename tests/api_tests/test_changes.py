import pytest

# Allow everything in here to access the DB
pytestmark = pytest.mark.django_db

import logging

from rest_framework import status

from .util import (
    get_result,
)

log = logging.getLogger(__name__)


def test_filter_by_event(client, site):
    """Test filtering changes by event type."""
    dev_uri = site.list_uri("device")
    change_uri = site.list_uri("change")

    # Create a device (generates a "Create" change)
    client.create(dev_uri, hostname="chg-test1")

    # Filter for Create events
    resp = client.get(change_uri, params={"event": "Create"})
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    # Should include Device and Site creates
    assert len(results) >= 1
    assert all(r["event"] == "Create" for r in results)


def test_filter_by_resource_name(client, site):
    """Test filtering changes by resource_name."""
    dev_uri = site.list_uri("device")
    change_uri = site.list_uri("change")

    client.create(dev_uri, hostname="chg-test1")

    resp = client.get(change_uri, params={"resource_name": "Device"})
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    assert len(results) >= 1
    assert all(r["resource_name"] == "Device" for r in results)


def test_filter_by_user(client, site):
    """Test filtering changes by user id."""
    dev_uri = site.list_uri("device")
    change_uri = site.list_uri("change")

    client.create(dev_uri, hostname="chg-test1")

    # Get changes to find the user id
    resp = client.get(change_uri)
    results = get_result(resp)
    user_field = results[0]["user"]
    # user may be an int (pk) or a dict with "id"
    user_id = user_field["id"] if isinstance(user_field, dict) else user_field

    # Filter by user
    resp = client.get(change_uri, params={"user": user_id})
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    assert len(results) >= 1
    for r in results:
        r_user = r["user"]["id"] if isinstance(r["user"], dict) else r["user"]
        assert r_user == user_id


def test_filter_by_user_no_match(client, site):
    """Test filtering changes by non-existent user returns empty."""
    change_uri = site.list_uri("change")

    resp = client.get(change_uri, params={"user": 99999})
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    assert len(results) == 0


def test_filter_by_change_at_gte(client, site):
    """Test filtering changes with change_at__gte."""
    change_uri = site.list_uri("change")

    # Use a date far in the past; should return all changes
    resp = client.get(
        change_uri, params={"change_at__gte": "2000-01-01T00:00:00Z"}
    )
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    assert len(results) >= 1  # At least the Site create


def test_filter_by_change_at_lte(client, site):
    """Test filtering changes with change_at__lte."""
    change_uri = site.list_uri("change")

    # Use a date far in the past; should return no changes
    resp = client.get(
        change_uri, params={"change_at__lte": "2000-01-01T00:00:00Z"}
    )
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    assert len(results) == 0


def test_filter_by_date_range(client, site):
    """Test filtering changes with both change_at__gte and change_at__lte."""
    change_uri = site.list_uri("change")

    # Wide range should return results
    resp = client.get(
        change_uri,
        params={
            "change_at__gte": "2000-01-01T00:00:00Z",
            "change_at__lte": "2099-01-01T00:00:00Z",
        },
    )
    results = get_result(resp)
    assert resp.status_code == status.HTTP_200_OK
    assert len(results) >= 1
