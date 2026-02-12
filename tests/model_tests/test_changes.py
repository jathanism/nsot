import json

import pytest

from nsot import models

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db


@pytest.fixture
def create(device, user):
    models.Change.objects.create(event="Create", obj=device, user=user)


# ---- Text diff tests ----


def test_diff_device_hostname(create, device, user):
    device.hostname = "foo-bar3"
    device.save()
    update = models.Change.objects.create(
        event="Update", obj=device, user=user
    )

    assert '-   "hostname": "foo-bar1"' in update.diff
    assert '+   "hostname": "foo-bar3"' in update.diff


def test_diff_noop(create, device, user):
    update = models.Change.objects.create(
        event="Update", obj=device, user=user
    )

    blob = json.dumps(update.resource, indent=2, sort_keys=True)

    for line_a, line_b in zip(
        update.diff.splitlines(), blob.splitlines(), strict=True
    ):
        assert line_a.strip() == line_b.strip()


def test_diff_delete(create, device, user):
    delete = models.Change.objects.create(
        event="Delete", obj=device, user=user
    )
    blob = json.dumps(delete.resource, indent=2, sort_keys=True)

    for line_a, line_b in zip(
        delete.diff.splitlines(), blob.splitlines(), strict=True
    ):
        assert line_a == "- " + line_b


# ---- JSON resource_diff tests ----


def test_resource_diff_create(device, user):
    create_change = models.Change.objects.create(
        event="Create", obj=device, user=user
    )
    diff = create_change.resource_diff

    # Every field should appear with old=None
    for key, value in create_change.resource.items():
        assert key in diff
        assert diff[key]["old"] is None
        assert diff[key]["new"] == value


def test_resource_diff_update(create, device, user):
    device.hostname = "foo-bar3"
    device.save()
    update = models.Change.objects.create(
        event="Update", obj=device, user=user
    )
    diff = update.resource_diff

    # Only the changed field should appear
    assert "hostname" in diff
    assert diff["hostname"]["old"] == "foo-bar1"
    assert diff["hostname"]["new"] == "foo-bar3"

    # Unchanged fields should not appear
    assert "site_id" not in diff


def test_resource_diff_update_noop(create, device, user):
    update = models.Change.objects.create(
        event="Update", obj=device, user=user
    )
    diff = update.resource_diff

    # No fields changed, diff should be empty
    assert diff == {}


def test_resource_diff_delete(create, device, user):
    delete = models.Change.objects.create(
        event="Delete", obj=device, user=user
    )
    diff = delete.resource_diff

    # Every field should appear with new=None, old from self._resource
    for key, value in delete.resource.items():
        assert key in diff
        assert diff[key]["old"] == value
        assert diff[key]["new"] is None


def test_resource_diff_update_no_prior_change(device, user):
    # Create an Update change without a prior Create change
    update = models.Change.objects.create(
        event="Update", obj=device, user=user
    )
    diff = update.resource_diff

    # With no prior change, all fields should have old=None
    for key, value in update.resource.items():
        assert key in diff
        assert diff[key]["old"] is None
        assert diff[key]["new"] == value
