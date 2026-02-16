"""Tests for the ``expires_at`` field and queryset helpers on Resource models."""

from datetime import timedelta

import pytest
from django.utils import timezone

from nsot import models

pytestmark = pytest.mark.django_db


@pytest.fixture
def site():
    return models.Site.objects.create(name="Test Site")


@pytest.fixture
def devices(site):
    """Create devices with various expiry states."""
    now = timezone.now()
    return {
        "no_expiry": models.Device.objects.create(
            hostname="no-expiry", site=site
        ),
        "expired": models.Device.objects.create(
            hostname="expired", site=site, expires_at=now - timedelta(hours=1)
        ),
        "future": models.Device.objects.create(
            hostname="future", site=site, expires_at=now + timedelta(days=30)
        ),
        "soon": models.Device.objects.create(
            hostname="soon", site=site, expires_at=now + timedelta(days=3)
        ),
        "boundary": models.Device.objects.create(
            hostname="boundary", site=site, expires_at=now + timedelta(days=7)
        ),
    }


class TestExpiredQuerySet:
    """Tests for ResourceSetTheoryQuerySet.expired()."""

    def test_expired_true_returns_past(self, devices):
        qs = models.Device.objects.expired(expired=True)
        hostnames = set(qs.values_list("hostname", flat=True))
        assert "expired" in hostnames
        assert "future" not in hostnames
        assert "no-expiry" not in hostnames

    def test_expired_false_returns_non_expired(self, devices):
        qs = models.Device.objects.expired(expired=False)
        hostnames = set(qs.values_list("hostname", flat=True))
        assert "no-expiry" in hostnames
        assert "future" in hostnames
        assert "soon" in hostnames
        assert "expired" not in hostnames

    def test_expired_default_is_true(self, devices):
        qs = models.Device.objects.expired()
        hostnames = set(qs.values_list("hostname", flat=True))
        assert "expired" in hostnames
        assert "no-expiry" not in hostnames

    def test_null_expires_at_not_expired(self, devices):
        """Resources with null expires_at should never appear as expired."""
        qs = models.Device.objects.expired(expired=True)
        assert not qs.filter(hostname="no-expiry").exists()


class TestExpiringWithinDays:
    """Tests for ResourceSetTheoryQuerySet.expiring_within_days()."""

    def test_default_7_days(self, devices):
        qs = models.Device.objects.expiring_within_days()
        hostnames = set(qs.values_list("hostname", flat=True))
        assert "soon" in hostnames  # 3 days out
        assert "boundary" in hostnames  # 7 days out (lte cutoff)
        assert "future" not in hostnames  # 30 days out
        assert "expired" not in hostnames  # already expired
        assert "no-expiry" not in hostnames  # no expiry

    def test_custom_days(self, devices):
        qs = models.Device.objects.expiring_within_days(days=2)
        hostnames = set(qs.values_list("hostname", flat=True))
        assert "soon" not in hostnames  # 3 days > 2 days
        assert "future" not in hostnames

    def test_already_expired_excluded(self, devices):
        qs = models.Device.objects.expiring_within_days(days=365)
        assert not qs.filter(hostname="expired").exists()


class TestExpiresAtField:
    """Basic field behavior tests."""

    def test_default_is_none(self, site):
        dev = models.Device.objects.create(hostname="test-default", site=site)
        assert dev.expires_at is None

    def test_set_and_read(self, site):
        ts = timezone.now() + timedelta(days=10)
        dev = models.Device.objects.create(
            hostname="test-set", site=site, expires_at=ts
        )
        dev.refresh_from_db()
        # Compare to within a second (DB may truncate microseconds)
        assert abs((dev.expires_at - ts).total_seconds()) < 1
