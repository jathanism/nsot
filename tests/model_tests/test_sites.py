import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import logging

from django.core.exceptions import ValidationError as DjangoValidationError

from nsot import exc, models

log = logging.getLogger(__name__)


def test_site_creation():
    site = models.Site.objects.create(
        name="Test Site", description="This is a Test Site."
    )
    sites = models.Site.objects.all()

    assert sites.count() == 1
    assert sites[0].id == site.id
    assert sites[0].name == site.name
    assert sites[0].description == site.description


def test_site_conflict(transactional_db):
    models.Site.objects.create(
        name="Test Site", description="This is a Test Site."
    )

    with pytest.raises(DjangoValidationError):
        models.Site.objects.create(
            name="Test Site", description="This is a Test Site."
        )

    models.Site.objects.create(
        name="Test Site 2", description="This is a Test Site."
    )


def test_site_validation(transactional_db):
    with pytest.raises(exc.ValidationError):
        models.Site.objects.create(
            name=None, description="This is a Test Site."
        )

    with pytest.raises(exc.ValidationError):
        models.Site.objects.create(name="", description="This is a Test Site.")

    site = models.Site.objects.create(
        name="Test Site", description="This is a Test Site."
    )

    with pytest.raises(exc.ValidationError):
        site.name = ""
        site.save()

    with pytest.raises(exc.ValidationError):
        site.name = None
        site.save()

    site.name = "Test Site New"
    site.save()


def test_site_emoji_description():
    """Test that emoji/unicode characters in Site description don't cause errors.

    Ref: https://github.com/jathanism/nsot/issues/56
    """
    description = "This is a site with emoji 🎉🚀💡 and unicode ñ é ü"
    site = models.Site.objects.create(
        name="Emoji Site", description=description
    )
    site.refresh_from_db()

    assert site.description == description


def test_site_emoji_name_and_description():
    """Test that emoji/unicode characters work in both name and description."""
    site = models.Site.objects.create(
        name="Site ✨", description="Description with 🌍🔥 emojis"
    )
    site.refresh_from_db()

    assert site.name == "Site ✨"
    assert site.description == "Description with 🌍🔥 emojis"
