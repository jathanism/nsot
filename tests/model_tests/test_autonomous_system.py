import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

from django.core.exceptions import ValidationError

from nsot import exc, models


def test_create_autonomous_system(site):
    """Test basic creation of an AutonomousSystem."""
    asn = models.AutonomousSystem.objects.create(
        site=site, number=65001, description="Test ASN"
    )
    assert asn.number == 65001
    assert asn.description == "Test ASN"
    assert asn.site == site


def test_unique_constraint(site):
    """Test that duplicate (site, number) raises ValidationError."""
    models.AutonomousSystem.objects.create(site=site, number=65001)
    with pytest.raises(ValidationError):
        models.AutonomousSystem.objects.create(site=site, number=65001)


def test_validation_number_zero(site):
    """Test that number=0 raises ValidationError."""
    with pytest.raises(exc.ValidationError):
        models.AutonomousSystem.objects.create(site=site, number=0)


def test_validation_number_max(site):
    """Test that number=4294967295 raises ValidationError."""
    with pytest.raises(exc.ValidationError):
        models.AutonomousSystem.objects.create(site=site, number=4294967295)


def test_validation_number_min_valid(site):
    """Test that number=1 is valid."""
    asn = models.AutonomousSystem.objects.create(site=site, number=1)
    assert asn.number == 1


def test_validation_number_max_valid(site):
    """Test that number=4294967294 is valid."""
    asn = models.AutonomousSystem.objects.create(site=site, number=4294967294)
    assert asn.number == 4294967294


def test_str(site):
    """Test __str__ returns 'AS65001'."""
    asn = models.AutonomousSystem.objects.create(site=site, number=65001)
    assert str(asn) == "AS65001"


def test_number_asdot_16bit(site):
    """Test number_asdot for 16-bit ASN returns plain string."""
    asn = models.AutonomousSystem.objects.create(site=site, number=65001)
    assert asn.number_asdot == "65001"


def test_number_asdot_32bit(site):
    """Test number_asdot for 32-bit ASN returns hi.lo notation."""
    asn = models.AutonomousSystem.objects.create(site=site, number=65536)
    assert asn.number_asdot == "1.0"

    asn2 = models.AutonomousSystem.objects.create(site=site, number=131072)
    assert asn2.number_asdot == "2.0"

    asn3 = models.AutonomousSystem.objects.create(site=site, number=65537)
    assert asn3.number_asdot == "1.1"


def test_to_dict(site):
    """Test to_dict() includes all expected keys."""
    asn = models.AutonomousSystem.objects.create(
        site=site, number=65001, description="Test"
    )
    d = asn.to_dict()
    assert set(d.keys()) == {
        "id",
        "site_id",
        "number",
        "description",
        "attributes",
    }
    assert d["number"] == 65001
    assert d["description"] == "Test"
    assert d["site_id"] == site.id
    assert d["attributes"] == {}


def test_clean_number(site):
    """Test clean_number validation directly."""
    asn = models.AutonomousSystem(site=site, number=65001)
    assert asn.clean_number(65001) == 65001

    with pytest.raises(exc.ValidationError):
        asn.clean_number(0)

    with pytest.raises(exc.ValidationError):
        asn.clean_number(4294967295)

    with pytest.raises(exc.ValidationError):
        asn.clean_number(None)


def test_attributes(site):
    """Test setting and getting attributes on an AutonomousSystem."""
    models.Attribute.objects.create(
        site=site, resource_name="AutonomousSystem", name="owner"
    )
    asn = models.AutonomousSystem.objects.create(
        site=site, number=65001, attributes={"owner": "jathan"}
    )
    assert asn.get_attributes() == {"owner": "jathan"}
