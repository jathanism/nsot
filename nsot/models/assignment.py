from django.db import models

from .. import exc, validators


class Assignment(models.Model):
    """
    DB object for assignment of addresses to interfaces (on devices).

    This is used to enforce constraints at the relationship level for addition
    of new address assignments.
    """

    address = models.ForeignKey(
        "Network",
        related_name="assignments",
        db_index=True,
        on_delete=models.CASCADE,
        help_text="Network to which this assignment is bound.",
    )
    interface = models.ForeignKey(
        "Interface",
        related_name="assignments",
        db_index=True,
        on_delete=models.CASCADE,
        help_text="Interface to which this assignment is bound.",
    )
    created = models.DateTimeField(auto_now_add=True)

    def __sr__(self):
        return "interface=%s, address=%s" % (self.interface, self.address)

    class Meta:
        unique_together = ("address", "interface")

    def clean_address(self, value):
        """Enforce that new addresses can only be host addresses."""
        addr = validators.validate_host_address(value)

        # Enforce uniqueness upon assignment.
        existing = Assignment.objects.filter(address=addr)
        if existing.filter(interface__device=self.interface.device).exists():
            raise exc.ValidationError(
                {"address": "Address already assigned to this Device."}
            )

        return value

    def clean_fields(self, exclude=None):
        self.clean_address(self.address)
        self.address.set_assigned()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "device": self.interface.device.id,
            "hostname": self.interface.device_hostname,
            "interface": self.interface.id,
            "interface_name": self.interface.name,
            "address": self.address.cidr,
        }


def revert_network_state_on_assignment_delete(sender, instance, **kwargs):
    """Revert Network state to ALLOCATED when no assignments remain."""
    from .network import Network

    try:
        address = Network.objects.get(pk=instance.address_id)
    except Network.DoesNotExist:
        return  # Network deleted too (e.g., _purge_addresses cascade)
    if not address.assignments.exists():
        address.set_allocated()


models.signals.post_delete.connect(
    revert_network_state_on_assignment_delete,
    sender=Assignment,
    dispatch_uid="revert_network_state_post_delete_assignment",
)
