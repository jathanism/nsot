"""Tests for Attribute dependency (depends_on) functionality."""

import pytest

pytestmark = pytest.mark.django_db

from nsot import exc, models


@pytest.fixture
def site():
    return models.Site.objects.create(
        name="Test Site", description="Test Site."
    )


@pytest.fixture
def site2():
    return models.Site.objects.create(
        name="Other Site", description="Other Site."
    )


def _mkattr(site, name, resource_name="Device", **kwargs):
    return models.Attribute.objects.create(
        site=site, name=name, resource_name=resource_name, **kwargs
    )


class TestDependencyCreation:
    def test_basic_dependency(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)
        a.validate_dependencies()
        assert list(a.depends_on.all()) == [b]

    def test_get_all_dependencies_transitive(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        c = _mkattr(site, "c")
        a.depends_on.add(b)
        b.depends_on.add(c)
        deps = a.get_all_dependencies()
        assert set(deps) == {b, c}

    def test_self_reference_rejected(self, site):
        a = _mkattr(site, "a")
        a.depends_on.add(a)
        with pytest.raises(
            exc.ValidationError, match="cannot depend on itself"
        ):
            a.validate_dependencies()

    def test_cycle_ab_rejected(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)
        a.validate_dependencies()
        b.depends_on.add(a)
        with pytest.raises(exc.ValidationError, match="Circular dependency"):
            b.validate_dependencies()

    def test_longer_cycle_rejected(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        c = _mkattr(site, "c")
        a.depends_on.add(b)
        b.depends_on.add(c)
        c.depends_on.add(a)
        with pytest.raises(exc.ValidationError, match="Circular dependency"):
            c.validate_dependencies()

    def test_cross_resource_name_rejected(self, site):
        a = _mkattr(site, "a", resource_name="Device")
        b = _mkattr(site, "b", resource_name="Network")
        a.depends_on.add(b)
        with pytest.raises(exc.ValidationError, match="resource type"):
            a.validate_dependencies()

    def test_cross_site_rejected(self, site, site2):
        a = _mkattr(site, "a")
        b = _mkattr(site2, "b")
        a.depends_on.add(b)
        with pytest.raises(exc.ValidationError, match="different site"):
            a.validate_dependencies()


class TestDeletionProtection:
    def test_delete_with_dependents_blocked(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)
        with pytest.raises(exc.ValidationError, match="Cannot delete"):
            b.delete()

    def test_delete_without_dependents_succeeds(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)
        # a has no dependents, so it can be deleted
        a.delete()
        assert (
            models.Attribute.objects.filter(name="a", site=site).count() == 0
        )


class TestSetAttributesDependencies:
    """Test dependency enforcement in Resource.set_attributes()."""

    def test_missing_direct_dependency(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)

        device = models.Device.objects.create(site=site, hostname="dev1")
        with pytest.raises(exc.ValidationError, match="requires"):
            device.set_attributes({"a": "val"})

    def test_missing_transitive_dependency(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        c = _mkattr(site, "c")
        a.depends_on.add(b)
        b.depends_on.add(c)

        device = models.Device.objects.create(site=site, hostname="dev1")
        with pytest.raises(exc.ValidationError, match="requires"):
            device.set_attributes({"a": "val", "b": "val"})

    def test_defaults_satisfy_dependencies(self, site):
        b = _mkattr(site, "b")
        b.default = "default_val"
        b.save()
        a = _mkattr(site, "a")
        a.depends_on.add(b)

        device = models.Device.objects.create(site=site, hostname="dev1")
        device.set_attributes({"a": "val"})
        attrs = device.get_attributes()
        assert attrs["a"] == "val"
        assert attrs["b"] == "default_val"

    def test_all_deps_present_succeeds(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)

        device = models.Device.objects.create(site=site, hostname="dev1")
        device.set_attributes({"a": "val", "b": "val2"})
        attrs = device.get_attributes()
        assert attrs["a"] == "val"
        assert attrs["b"] == "val2"

    def test_no_dependencies_unchanged(self, site):
        _mkattr(site, "a")
        device = models.Device.objects.create(site=site, hostname="dev1")
        device.set_attributes({"a": "val"})
        assert device.get_attributes()["a"] == "val"

    def test_partial_update_remove_depended_on_fails(self, site):
        a = _mkattr(site, "a")
        b = _mkattr(site, "b")
        a.depends_on.add(b)

        device = models.Device.objects.create(site=site, hostname="dev1")
        device.set_attributes({"a": "val", "b": "val2"})

        # Try to remove b via null in partial update
        with pytest.raises(exc.ValidationError, match="requires"):
            device.set_attributes({"b": None}, partial=True)
