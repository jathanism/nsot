from django.conf import settings
from django.db import models

from .. import exc
from .circuit import Circuit
from .resource import Resource


class Device(Resource):
    """Represents a network device."""

    hostname = models.CharField(
        max_length=255,
        null=False,
        db_index=True,
        help_text="The hostname of the Device.",
    )
    site = models.ForeignKey(
        "Site",
        db_index=True,
        related_name="devices",
        on_delete=models.PROTECT,
        verbose_name="Site",
        help_text="Unique ID of the Site this Device is under.",
    )

    def __str__(self):
        return "%s" % self.hostname

    class Meta:
        unique_together = ("site", "hostname")

    @property
    def circuits(self):
        """All circuits related to this Device."""
        interfaces = self.interfaces.all()
        circuits = []
        for intf in interfaces:
            try:
                circuits.append(intf.circuit)
            except Circuit.DoesNotExist:
                continue
        return circuits

    def clean_hostname(self, value):
        if not value:
            raise exc.ValidationError(
                {"hostname": "Hostname must be non-zero length string."}
            )
        if len(value) > 253:
            raise exc.ValidationError(
                {"hostname": "Hostname exceeds 253-character FQDN limit."}
            )
        if not settings.DEVICE_NAME.match(value):
            raise exc.ValidationError(
                {"hostname": "Invalid hostname: %r." % value}
            )
        return value

    def clean_fields(self, exclude=None):
        self.hostname = self.clean_hostname(self.hostname)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "hostname": self.hostname,
            "attributes": self.get_attributes(),
        }
