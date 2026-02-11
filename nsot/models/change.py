import difflib
import json
from calendar import timegm

from django.conf import settings
from django.db import models

from .. import exc, fields
from . import constants
from .site import Site


class Change(models.Model):
    """Record of all changes in NSoT."""

    site = models.ForeignKey(
        "Site",
        db_index=True,
        related_name="changes",
        verbose_name="Site",
        on_delete=models.CASCADE,
        help_text="Unique ID of the Site this Change is under.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="changes",
        db_index=True,
        on_delete=models.CASCADE,
        help_text="The User that initiated this Change.",
    )
    change_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        null=False,
        help_text="The timestamp of this Change.",
    )
    event = models.CharField(
        max_length=10,
        null=False,
        choices=constants.EVENT_CHOICES,
        help_text="The type of event this Change represents.",
    )
    resource_id = models.IntegerField(
        "Resource ID",
        null=False,
        help_text="The unique ID of the Resource for this Change.",
    )
    resource_name = models.CharField(
        "Resource Type",
        max_length=20,
        null=False,
        db_index=True,
        choices=constants.CHANGE_RESOURCE_CHOICES,
        help_text="The name of the Resource for this Change.",
    )
    _resource = fields.JSONField(
        "Resource",
        null=False,
        blank=True,
        help_text="Local cache of the changed Resource. (Internal use only)",
    )

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.pop("obj", None)
        super().__init__(*args, **kwargs)

    class Meta:
        get_latest_by = "change_at"
        indexes = [
            models.Index(fields=["resource_name", "resource_id"]),
            models.Index(fields=["resource_name", "event"]),
        ]

    def __str__(self):
        return "%s %s(%s)" % (self.event, self.resource_name, self.resource_id)

    @property
    def resource(self):
        return self._resource

    def get_change_at(self):
        return timegm(self.change_at.timetuple())

    get_change_at.short_description = "Change At"

    @classmethod
    def get_serializer_for_resource(cls, resource_name):
        from ..api import serializers

        serializer_class = resource_name + "Serializer"
        return getattr(serializers, serializer_class)

    def clean_event(self, value):
        if value not in constants.CHANGE_EVENTS:
            raise exc.ValidationError("Invalid change event: %r." % value)
        return value

    def clean_resource_name(self, value):
        if value not in constants.VALID_CHANGE_RESOURCES:
            raise exc.ValidationError("Invalid resource name: %r." % value)
        return value

    def clean_site(self, obj):
        """value in this case is an instance of a model object."""

        # Site doesn't have an id to itself, so if obj is a Site, use it.
        # Otherwise get the value of the `.site`
        return obj if isinstance(obj, Site) else obj.site

    def clean_fields(self, exclude=None):
        """This will populate the change fields from the incoming object."""
        obj = self._obj
        if obj is None:
            return

        self.event = self.clean_event(self.event)
        self.resource_name = self.clean_resource_name(obj.__class__.__name__)
        self.resource_id = obj.id
        self.site = self.clean_site(obj)

        serializer_class = self.get_serializer_for_resource(self.resource_name)
        serializer = serializer_class(obj)
        self._resource = serializer.data

    def save(self, *args, **kwargs):
        self.full_clean()  # First validate fields are correct
        super().save(*args, **kwargs)

    def to_dict(self):
        resource = None
        if self.resource is not None:
            resource = self.resource

        return {
            "id": self.id,
            "site": self.site.to_dict(),
            "user": self.user.to_dict(),
            "change_at": timegm(self.change_at.timetuple()),
            "event": self.event,
            "resource_name": self.resource_name,
            "resource_id": self.resource_id,
            "resource": resource,
            "resource_diff": self.resource_diff,
        }

    def _get_previous_change(self):
        """Return the most recent prior Change for the same resource, or
        None."""
        return (
            Change.objects.filter(
                change_at__lt=self.change_at,
                resource_id=self.resource_id,
                resource_name=self.resource_name,
            )
            .order_by("-change_at")
            .first()
        )

    @property
    def resource_diff(self):
        """Return a dict of changed fields with old/new values."""
        if self.event == "Create":
            return {
                k: {"old": None, "new": v} for k, v in self._resource.items()
            }

        if self.event == "Delete":
            prev = self._get_previous_change()
            old_resource = prev._resource if prev else self._resource
            return {
                k: {"old": v, "new": None} for k, v in old_resource.items()
            }

        # Update — show only changed fields
        prev = self._get_previous_change()
        if prev is None:
            return {
                k: {"old": None, "new": v} for k, v in self._resource.items()
            }

        diff = {}
        all_keys = set(prev._resource) | set(self._resource)
        for key in all_keys:
            old_val = prev._resource.get(key)
            new_val = self._resource.get(key)
            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}
        return diff

    @property
    def diff(self):
        """Return a text diff between previous and current resource state."""
        if self.event == "Create":
            old = ""
        else:
            prev = self._get_previous_change()
            old = (
                json.dumps(prev._resource, indent=2, sort_keys=True)
                if prev
                else ""
            )

        if self.event == "Delete":
            current = ""
        else:
            current = json.dumps(self._resource, indent=2, sort_keys=True)

        return "\n".join(difflib.ndiff(old.splitlines(), current.splitlines()))
