import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db


from nsot import exc, models


def test_device_attributes(site):
    models.Attribute.objects.create(
        site=site, resource_name="Device", name="owner"
    )

    device = models.Device.objects.create(
        site=site, hostname="foobarhost", attributes={"owner": "gary"}
    )

    assert device.get_attributes() == {"owner": "gary"}

    # Verify property successfully zeros out attributes
    device.set_attributes({})
    assert device.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        device.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        device.set_attributes({0: "value"})

    with pytest.raises(exc.ValidationError):
        device.set_attributes({"key": 0})

    with pytest.raises(exc.ValidationError):
        device.set_attributes({"made_up": "value"})


def test_retrieve_device(site):
    models.Attribute.objects.create(
        site=site, resource_name="Device", name="test"
    )

    device1 = models.Device.objects.create(
        site=site, hostname="device1", attributes={"test": "foo"}
    )
    device2 = models.Device.objects.create(
        site=site, hostname="device2", attributes={"test": "bar"}
    )
    device3 = models.Device.objects.create(site=site, hostname="device3")

    assert list(site.devices.all()) == [device1, device2, device3]

    # Filter by attributes
    assert list(site.devices.by_attribute(None, "foo")) == []
    assert list(site.devices.by_attribute("test", "foo")) == [device1]


def test_validation(site, transactional_db):
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site,
            hostname=None,
        )

    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site,
            hostname="a b",
        )

    device = models.Device.objects.create(site=site, hostname="testhost")

    with pytest.raises(exc.ValidationError):
        device.hostname = ""
        device.save()

    with pytest.raises(exc.ValidationError):
        device.hostname = None
        device.save()

    device.hostname = "newtesthostname"
    device.save()


def test_fqdn_validation(site):
    """Test FQDN hostnames are accepted and invalid ones rejected."""
    # Simple hostname still works (backward compat)
    d1 = models.Device.objects.create(site=site, hostname="router1")
    assert d1.hostname == "router1"

    # Basic FQDN
    d2 = models.Device.objects.create(
        site=site, hostname="router1.example.com"
    )
    assert d2.hostname == "router1.example.com"

    # Real-world FQDN from bug report (dropbox/nsot#264)
    d_real = models.Device.objects.create(
        site=site, hostname="TIJ-S5320.36C.EI.28S.DC-SW00294"
    )
    assert d_real.hostname == "TIJ-S5320.36C.EI.28S.DC-SW00294"

    # Multi-level FQDN
    d3 = models.Device.objects.create(
        site=site, hostname="sw1.pop.region.example.com"
    )
    assert d3.hostname == "sw1.pop.region.example.com"

    # Single-char labels
    d4 = models.Device.objects.create(site=site, hostname="a.b.c")
    assert d4.hostname == "a.b.c"

    # Trailing dot rejected
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site, hostname="router1.example.com."
        )

    # Leading dot rejected
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site, hostname=".router1.example.com"
        )

    # Consecutive dots rejected
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site, hostname="router1..example.com"
        )

    # Label >63 chars rejected
    long_label = "a" * 64
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site, hostname=f"{long_label}.example.com"
        )

    # Total >253 chars rejected
    # Build a valid-looking FQDN that exceeds 253 chars
    label = "a" * 63
    fqdn = ".".join([label] * 4)  # 63*4 + 3 dots = 255 chars
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(site=site, hostname=fqdn)

    # Spaces rejected
    with pytest.raises(exc.ValidationError):
        models.Device.objects.create(
            site=site, hostname="router 1.example.com"
        )
