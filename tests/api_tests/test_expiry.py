"""API tests for expires_at field — filters and CRUD."""

from datetime import datetime, timedelta
from datetime import timezone as dt_tz

import pytest
from rest_framework import status

from .util import (
    get_result,
)

pytestmark = pytest.mark.django_db


def _iso(dt):
    """Format a datetime as ISO 8601 string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _now():
    return datetime.now(tz=dt_tz.utc)


@pytest.fixture
def setup(client, site):
    """Create devices with various expiry states for filter tests."""
    dev_uri = site.list_uri("device")
    now = _now()

    devs = {}
    for name, offset in [
        ("no-expiry", None),
        ("expired", timedelta(hours=-1)),
        ("future", timedelta(days=30)),
        ("soon", timedelta(days=3)),
    ]:
        kwargs = {"hostname": name}
        if offset is not None:
            kwargs["expires_at"] = _iso(now + offset)
        resp = client.create(dev_uri, **kwargs)
        assert resp.status_code == status.HTTP_201_CREATED, resp.json()
        devs[name] = get_result(resp)

    return {"devs": devs, "dev_uri": dev_uri, "site": site}


class TestExpiryFilters:
    """Test ?expired, ?expires_before, ?expires_after query params."""

    def test_unfiltered_returns_all(self, client, setup):
        resp = client.get(setup["dev_uri"])
        results = get_result(resp)
        assert len(results) == 4

    def test_expired_true(self, client, setup):
        resp = client.get(setup["dev_uri"], params={"expired": "true"})
        results = get_result(resp)
        hostnames = {d["hostname"] for d in results}
        assert hostnames == {"expired"}

    def test_expired_false(self, client, setup):
        resp = client.get(setup["dev_uri"], params={"expired": "false"})
        results = get_result(resp)
        hostnames = {d["hostname"] for d in results}
        assert "expired" not in hostnames
        assert "no-expiry" in hostnames
        assert "future" in hostnames

    def test_expires_before(self, client, setup):
        cutoff = _iso(_now() + timedelta(days=5))
        resp = client.get(setup["dev_uri"], params={"expires_before": cutoff})
        results = get_result(resp)
        hostnames = {d["hostname"] for d in results}
        assert "soon" in hostnames
        assert "expired" in hostnames
        assert "future" not in hostnames

    def test_expires_after(self, client, setup):
        cutoff = _iso(_now() + timedelta(days=5))
        resp = client.get(setup["dev_uri"], params={"expires_after": cutoff})
        results = get_result(resp)
        hostnames = {d["hostname"] for d in results}
        assert "future" in hostnames
        assert "soon" not in hostnames


class TestExpiryCRUD:
    """Test create, update, patch with expires_at."""

    def test_create_with_expires_at(self, client, site):
        dev_uri = site.list_uri("device")
        ts = _iso(_now() + timedelta(days=10))
        resp = client.create(dev_uri, hostname="with-expiry", expires_at=ts)
        assert resp.status_code == status.HTTP_201_CREATED
        result = get_result(resp)
        assert result["expires_at"] is not None

    def test_create_without_expires_at(self, client, site):
        dev_uri = site.list_uri("device")
        resp = client.create(dev_uri, hostname="no-expiry-create")
        assert resp.status_code == status.HTTP_201_CREATED
        result = get_result(resp)
        assert result["expires_at"] is None

    def test_patch_set_expires_at(self, client, site):
        dev_uri = site.list_uri("device")
        resp = client.create(dev_uri, hostname="patch-test")
        dev = get_result(resp)
        dev_detail = site.detail_uri("device", id=dev["id"])

        ts = _iso(_now() + timedelta(days=5))
        resp = client.partial_update(dev_detail, expires_at=ts)
        assert resp.status_code == status.HTTP_200_OK
        result = get_result(resp)
        assert result["expires_at"] is not None

    def test_patch_clear_expires_at(self, client, site):
        dev_uri = site.list_uri("device")
        ts = _iso(_now() + timedelta(days=5))
        resp = client.create(dev_uri, hostname="clear-test", expires_at=ts)
        dev = get_result(resp)
        dev_detail = site.detail_uri("device", id=dev["id"])

        resp = client.partial_update(dev_detail, expires_at=None)
        assert resp.status_code == status.HTTP_200_OK
        result = get_result(resp)
        assert result["expires_at"] is None
