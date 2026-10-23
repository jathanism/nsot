from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .. import exc
from .resource import Resource


class AutonomousSystem(Resource):
    """Represents an Autonomous System (AS) number resource."""

    number = models.PositiveBigIntegerField(
        null=False,
        db_index=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4294967294),
        ],
        help_text="The Autonomous System Number (ASN). Valid range: 1-4294967294.",
    )
    description = models.CharField(
        max_length=255,
        default="",
        blank=True,
        null=False,
        help_text="A brief description of this Autonomous System.",
    )
    site = models.ForeignKey(
        "Site",
        db_index=True,
        related_name="autonomous_systems",
        on_delete=models.PROTECT,
        verbose_name="Site",
        help_text="Unique ID of the Site this Autonomous System is under.",
    )

    class Meta:
        unique_together = ("site", "number")
        verbose_name = "Autonomous System"
        verbose_name_plural = "Autonomous Systems"

    def __str__(self):
        return "AS%d" % self.number

    @property
    def number_asdot(self):
        """Return ASDOT notation for this ASN.

        For 16-bit ASNs (< 65536), returns the plain number as a string.
        For 32-bit ASNs (>= 65536), returns ``hi.lo`` notation via
        ``divmod(number, 65536)``.
        """
        if self.number < 65536:
            return str(self.number)
        hi, lo = divmod(self.number, 65536)
        return "%d.%d" % (hi, lo)

    def clean_number(self, value):
        """Validate that ``value`` is within the valid ASN range (1-4294967294).

        :param value:
            ASN value to validate.

        :returns:
            The validated value.

        :raises exc.ValidationError:
            If the value is outside the valid range.
        """
        if value is None or value < 1 or value > 4294967294:
            raise exc.ValidationError(
                {
                    "number": "ASN must be between 1 and 4294967294, got: %r."
                    % value
                }
            )
        return value

    def clean_fields(self, exclude=None):
        self.number = self.clean_number(self.number)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "number": self.number,
            "description": self.description,
            "attributes": self.get_attributes(),
        }
