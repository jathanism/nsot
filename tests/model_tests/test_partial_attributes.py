"""Tests for partial attribute updates (PATCH behaviour)."""

import pytest

pytestmark = pytest.mark.django_db

from nsot import exc, models


@pytest.fixture
def device_with_attrs(site):
    """Create a device with two attributes pre-populated."""
    models.Attribute.objects.create(
        site=site, resource_name="Device", name="owner"
    )
    models.Attribute.objects.create(
        site=site, resource_name="Device", name="metro"
    )
    models.Attribute.objects.create(
        site=site, resource_name="Device", name="role"
    )
    device = models.Device.objects.create(
        site=site,
        hostname="partial-host",
        attributes={"owner": "jathan", "metro": "lax"},
    )
    return device


class TestPartialAttributeUpdate:
    """set_attributes(partial=True) should merge, not replace."""

    def test_partial_update_single_attr(self, device_with_attrs):
        """Updating one attribute preserves the others."""
        device_with_attrs.set_attributes({"owner": "gary"}, partial=True)
        attrs = device_with_attrs.get_attributes()
        assert attrs["owner"] == "gary"
        assert attrs["metro"] == "lax"

    def test_partial_add_new_attr(self, device_with_attrs):
        """Adding a new attribute via partial keeps existing ones."""
        device_with_attrs.set_attributes({"role": "br"}, partial=True)
        attrs = device_with_attrs.get_attributes()
        assert attrs == {"owner": "jathan", "metro": "lax", "role": "br"}

    def test_partial_delete_with_null(self, device_with_attrs):
        """Setting a value to None deletes that attribute."""
        device_with_attrs.set_attributes({"metro": None}, partial=True)
        attrs = device_with_attrs.get_attributes()
        assert attrs == {"owner": "jathan"}

    def test_partial_noop_when_no_attributes(self, device_with_attrs):
        """partial=True with None attributes is a no-op."""
        device_with_attrs.set_attributes(None, partial=True)
        assert device_with_attrs.get_attributes() == {
            "owner": "jathan",
            "metro": "lax",
        }

    def test_partial_invalid_attr_name(self, device_with_attrs):
        """Referencing a non-existent attribute raises ValidationError."""
        with pytest.raises(exc.ValidationError):
            device_with_attrs.set_attributes(
                {"nonexistent": "val"}, partial=True
            )

    def test_partial_skips_required_check(self, site):
        """partial=True should NOT error on missing required attributes."""
        models.Attribute.objects.create(
            site=site, resource_name="Device", name="req_attr", required=True
        )
        models.Attribute.objects.create(
            site=site, resource_name="Device", name="opt_attr"
        )
        device = models.Device.objects.create(
            site=site,
            hostname="req-host",
            attributes={"req_attr": "val1", "opt_attr": "val2"},
        )
        # Partial update without providing required attr should succeed.
        device.set_attributes({"opt_attr": "val3"}, partial=True)
        attrs = device.get_attributes()
        assert attrs == {"req_attr": "val1", "opt_attr": "val3"}

    def test_partial_cannot_delete_required(self, site):
        """partial=True should reject deletion of a required attribute."""
        models.Attribute.objects.create(
            site=site, resource_name="Device", name="req_attr", required=True
        )
        device = models.Device.objects.create(
            site=site,
            hostname="req-host2",
            attributes={"req_attr": "val1"},
        )
        # Attempting to delete a required attribute via null should fail.
        with pytest.raises(exc.ValidationError):
            device.set_attributes({"req_attr": None}, partial=True)


class TestFullAttributeUpdate:
    """set_attributes(partial=False) should still replace all (PUT behaviour)."""

    def test_full_update_replaces_all(self, device_with_attrs):
        """Full update replaces all attributes."""
        device_with_attrs.set_attributes({"role": "dr"})
        attrs = device_with_attrs.get_attributes()
        assert attrs == {"role": "dr"}

    def test_full_update_enforces_required(self, site):
        """Full update must include required attributes."""
        models.Attribute.objects.create(
            site=site, resource_name="Device", name="req", required=True
        )
        device = models.Device.objects.create(
            site=site, hostname="full-host", attributes={"req": "yes"}
        )
        with pytest.raises(exc.ValidationError):
            device.set_attributes({})
