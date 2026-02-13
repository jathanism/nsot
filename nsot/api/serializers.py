import ast
import json
import logging
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import fields, serializers
from rest_framework import validators as drf_validators

from nsot.vendor.rest_framework_bulk import (
    BulkListSerializer,
    BulkSerializerMixin,
)

from .. import exc, models, validators
from ..util import get_field_attr
from . import auth

log = logging.getLogger(__name__)


###############
# Custom Fields
###############
class JSONDataField(fields.Field):
    """
    Base field used to represent attributes as JSON <-> ``field_type``.

    It is an error if ``field_type`` is not defined in a subclass.
    """

    field_type = None

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        log.debug("JSONDictField.to_internal_value() data = %r", data)
        if self.field_type is None:
            raise NotImplementedError(
                "You must subclass JSONDataField and define field_type"
            )

        if not data:
            data = self.field_type()

        if isinstance(data, self.field_type):
            return data

        # Try it as a regular JSON object
        try:
            return json.loads(data)
        except ValueError:
            # Or try it as a Python object
            try:
                return ast.literal_eval(data)
            except (SyntaxError, ValueError) as err:
                raise exc.ValidationError(err)
        except Exception as err:
            raise exc.ValidationError(err)
        return data


class JSONDictField(JSONDataField):
    """Field used to represent attributes as JSON <-> Dict."""

    field_type = dict


class JSONListField(JSONDataField):
    """Field used to represent attributes as JSON <-> List."""

    field_type = list


class AttributeDefaultField(fields.Field):
    """
    Custom field for Attribute.default property.

    Handles serialization of the default value which can be a string (single)
    or list of strings (multi).
    """

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        # Pass through as-is — DRF handles JSON deserialization, model
        # validation (clean_default) enforces type correctness.
        return data


class MACAddressField(fields.Field):
    """Field used to validate MAC address objects as integer or string."""

    def to_representation(self, value):
        if value is None:
            return None
        return str(value)

    def to_internal_value(self, value):
        return validators.validate_mac_address(value)


class NaturalKeyRelatedField(serializers.SlugRelatedField):
    """Field that takes either a primary key or a natural key."""

    def to_representation(self, value):
        # When the source is a FK column (e.g. parent_id), DRF passes the raw
        # PK value (int) rather than the related object. Return it as-is.
        if isinstance(value, (int, str, type(None))):
            return value
        return getattr(value, self.slug_field)

    def to_internal_value(self, value):
        """Try PK followed by slug (natural key) value."""
        # Cast integers to strings, bruh
        if isinstance(value, int):
            value = str(value)

        # Is digit? Is PK.
        if value.isdigit():
            field = serializers.PrimaryKeyRelatedField(
                queryset=self.get_queryset()
            )
            log.debug(
                "NaturalKeyRelatedField: %s using PK field for value %s",
                self.field_name,
                value,
            )
        # Or it's natural key. Brute force!!
        else:
            field = serializers.SlugRelatedField(
                slug_field=self.slug_field,
                queryset=self.get_queryset(),
            )
            log.debug(
                "NaturalKeyRelatedField: %s using SLUG field for value %s",
                self.field_name,
                value,
            )

        value = field.to_internal_value(value)

        return value

    def get_queryset(self):
        """Attempt to filter queryset by site_pk."""
        queryset = super().get_queryset()
        view = self.context.get("view")

        # Get site_id from the view or None
        site_id = None if view is None else view.kwargs.get("site_pk")

        # Filter by site_id if applicable.
        if site_id is not None:
            log.debug("Filtering queryset to site_id=%s", site_id)
            queryset = queryset.filter(site_id=site_id)

        return queryset


###################
# Base Serializer #
###################
class NsotSerializer(serializers.ModelSerializer):
    """Base serializer that logs change events."""

    def to_internal_value(self, data):
        """Inject site_pk from view's kwargs if it's not already in data."""
        # Try to get the kwargs from the view, or default to empty kwargs.
        view = self.context.get("view")
        kwargs = getattr(view, "kwargs", {})

        log.debug(
            "NsotSerializer.to_internal_value() data [before] = %r", data
        )

        # FIXME(jathan): This MUST be ripped out once we migrate to V2 API and
        # move away from the "site_id" field on pre-1.0 objects.
        site_fields = ["site_id", "site"]
        for site_field in site_fields:
            if site_field in self.fields:
                break
        else:
            site_field = None

        if site_field not in data and "site_pk" in kwargs:
            data = data.copy()  # Get a mutable copy of the QueryDict
            data[site_field] = kwargs["site_pk"]

        log.debug("NsotSerializer.to_internal_value() data [after] = %r", data)

        return super().to_internal_value(data)

    def to_representation(self, obj):
        """Use DRF's standard field-based serialization."""
        if isinstance(obj, OrderedDict):
            return obj

        return super().to_representation(obj)


class WriteSerializerMixin:
    """Mixin for create/update serializers that delegates read output to the
    corresponding read serializer.

    Subclasses must define ``read_serializer_class`` pointing to the read
    serializer whose output format should be used for ``to_representation``.
    """

    read_serializer_class = None

    def to_representation(self, obj):
        if self.read_serializer_class is None:
            msg = f"{self.__class__.__name__} must set read_serializer_class"
            raise NotImplementedError(msg)
        return self.read_serializer_class(obj, context=self.context).data


######
# User
######
class UserSerializer(serializers.ModelSerializer):
    """
    UserProxy model serializer that takes optional `with_secret_key` argument
    that controls whether the secret_key for the user should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass `with_secret_key` up to the superclass
        self.with_secret_key = kwargs.pop("with_secret_key", None)
        super().__init__(*args, **kwargs)

        # If we haven't passed `with_secret_key`, don't show the secret_key
        # field.
        if self.with_secret_key is None:
            self.fields.pop("secret_key")

    permissions = fields.ReadOnlyField(source="get_permissions")

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "permissions", "secret_key")


######
# Site
######
class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Site
        fields = "__all__"


#########
# Changes
#########
class ChangeSerializer(NsotSerializer):
    """Used for displaying Change events."""

    site = SiteSerializer(read_only=True)
    user = serializers.SerializerMethodField(
        help_text="User who made this change.",
    )
    change_at = serializers.SerializerMethodField(
        help_text="Unix timestamp of when the change occurred.",
    )
    resource = serializers.SerializerMethodField(
        help_text="Full resource payload at the time of the change.",
    )

    class Meta:
        model = models.Change
        exclude = ["_resource"]

    def get_user(self, obj):
        return {"id": obj.user.id, "email": obj.user.email}

    def get_resource(self, obj):
        return obj.resource

    def get_change_at(self, obj):
        from calendar import timegm

        return timegm(obj.change_at.timetuple())

    def to_representation(self, obj):
        data = super().to_representation(obj)
        view = self.context.get("view")
        if view and getattr(view, "action", None) in ("retrieve", "diff"):
            data["resource_diff"] = obj.resource_diff
        return data


###########
# Attribute
###########
class AttributeSerializer(NsotSerializer):
    """Used for GET, DELETE on Attributes."""

    constraints = serializers.JSONField(read_only=True)
    default = serializers.JSONField(read_only=True)
    site_id = serializers.IntegerField(
        read_only=True,
        label=get_field_attr(models.Attribute, "site", "verbose_name"),
        help_text=get_field_attr(models.Attribute, "site", "help_text"),
    )

    class Meta:
        model = models.Attribute
        exclude = ["_default", "site"]


class AttributeCreateSerializer(WriteSerializerMixin, AttributeSerializer):
    """Used for POST on Attributes."""

    read_serializer_class = AttributeSerializer

    constraints = JSONDictField(
        required=False,
        label=get_field_attr(models.Attribute, "constraints", "verbose_name"),
        help_text=get_field_attr(models.Attribute, "constraints", "help_text"),
    )
    default = AttributeDefaultField(
        required=False,
        allow_null=True,
        help_text=get_field_attr(models.Attribute, "_default", "help_text"),
    )
    site_id = fields.IntegerField(
        label=get_field_attr(models.Attribute, "site", "verbose_name"),
        help_text=get_field_attr(models.Attribute, "site", "help_text"),
    )

    class Meta:
        model = models.Attribute
        fields = (
            "name",
            "description",
            "resource_name",
            "required",
            "display",
            "multi",
            "constraints",
            "default",
            "site_id",
        )


class AttributeUpdateSerializer(
    BulkSerializerMixin, AttributeCreateSerializer
):
    """
    Used for PUT, PATCH, on Attributes.

    Currently because Attributes have only one required field (name), and it
    may not be updated, there is not much functional difference between PUT and
    PATCH.
    """

    class Meta:
        model = models.Attribute
        list_serializer_class = BulkListSerializer
        fields = (
            "id",
            "description",
            "required",
            "display",
            "multi",
            "constraints",
            "default",
        )


############
# Assignment
############
class AssignmentSerializer(serializers.ModelSerializer):
    """Used for GET on Assignments (address-to-interface bindings)."""

    device = serializers.IntegerField(
        source="interface.device.id",
        read_only=True,
        help_text="ID of the Device this assignment belongs to.",
    )
    hostname = serializers.CharField(
        source="interface.device_hostname",
        read_only=True,
        help_text="Hostname of the Device this assignment belongs to.",
    )
    interface = serializers.IntegerField(
        source="interface.id",
        read_only=True,
        help_text="ID of the Interface this address is assigned to.",
    )
    interface_name = serializers.CharField(
        source="interface.name",
        read_only=True,
        help_text="Name of the Interface this address is assigned to.",
    )
    address = serializers.CharField(
        source="address.cidr",
        read_only=True,
        help_text="CIDR of the assigned address.",
    )

    class Meta:
        model = models.Assignment
        fields = (
            "id",
            "device",
            "hostname",
            "interface",
            "interface_name",
            "address",
        )


#######
# Value
#######
class ValueSerializer(serializers.ModelSerializer):
    """Used for GET, DELETE on Values."""

    class Meta:
        model = models.Value
        exclude = ["site"]


class ValueCreateSerializer(ValueSerializer):
    """Used for POST on Values."""

    class Meta(ValueSerializer.Meta):
        read_only_fields = ("id", "name", "resource_name")


###########
# Resources
###########
class ResourceSerializer(NsotSerializer):
    """For any object that can have attributes."""

    attributes = serializers.SerializerMethodField(
        help_text="Dictionary of attributes to set.",
    )
    site_id = serializers.PrimaryKeyRelatedField(
        source="site",
        queryset=models.Site.objects.all(),
        help_text="Unique ID of the Site this object is under.",
        label="Site",
    )

    def get_attributes(self, obj):
        return obj.get_attributes()

    def create(self, validated_data, commit=True):
        """Create that is aware of attributes."""
        # Remove the related fields before we write the object
        attributes = validated_data.pop("attributes", {})

        # Save the base object to the database.
        obj = super().create(validated_data)

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_attributes(attributes)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
            if commit:
                obj.save()

        return obj

    def update(self, instance, validated_data, commit=True):
        """
        Update that is aware of attributes.

        This will not set attributes if they are not provided during a partial
        update.
        """
        # Remove related fields before we write the object
        attributes = validated_data.pop("attributes", None)

        # Save the object to the database.
        obj = super().update(instance, validated_data)

        # If attributes have been provided, populate them and save the object,
        # allowing any validation errors to raise before saving.
        obj.set_attributes(attributes, partial=self.partial)

        if commit:
            obj.save()

        return obj


########
# Device
########
class DeviceSerializer(ResourceSerializer):
    """Used for GET, DELETE on Devices."""

    class Meta:
        model = models.Device
        exclude = ["_attributes_cache", "site"]


class DeviceCreateSerializer(WriteSerializerMixin, DeviceSerializer):
    """Used for POST on Devices."""

    read_serializer_class = DeviceSerializer

    # Override read-only SerializerMethodField with writable field for input.
    attributes = JSONDictField(
        required=False, help_text="Dictionary of attributes to set."
    )

    class Meta:
        model = models.Device
        fields = ("hostname", "attributes", "site_id")
        # TODO(jathan): Manaully set unique_together validator required due to
        # bug in DRF 3.11. Remove me in DRF 3.12 when it is fixed.
        # Ref: https://github.com/encode/django-rest-framework/issues/7100
        validators = [
            drf_validators.UniqueTogetherValidator(
                queryset=models.Device.objects.all(),
                fields=["site_id", "hostname"],
            )
        ]


class DevicePartialUpdateSerializer(
    BulkSerializerMixin, DeviceCreateSerializer
):
    """Used for PATCH on Devices."""

    class Meta:
        model = models.Device
        list_serializer_class = BulkListSerializer
        fields = ("id", "hostname", "attributes")


class DeviceUpdateSerializer(DevicePartialUpdateSerializer):
    """Used for PUT on Devices."""

    class Meta(DevicePartialUpdateSerializer.Meta):
        extra_kwargs = {"attributes": {"required": True}}


#########
# Network
#########
class NetworkSerializer(ResourceSerializer):
    """Used for GET, DELETE on Networks."""

    cidr = serializers.CharField(
        read_only=True,
        help_text="IPv4/IPv6 CIDR address.",
    )
    parent_id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text="ID of the parent Network, if any.",
    )
    parent = serializers.SerializerMethodField(
        help_text="CIDR of the parent Network, if any.",
    )
    is_ip = serializers.BooleanField(
        read_only=True,
        help_text="Whether this is a host address (/32 or /128).",
    )

    class Meta:
        model = models.Network
        exclude = ["_attributes_cache", "broadcast_address", "site"]

    def get_parent(self, obj):
        return obj.parent.cidr if obj.parent else None


class NetworkCreateSerializer(WriteSerializerMixin, NetworkSerializer):
    """Used for POST on Networks."""

    read_serializer_class = NetworkSerializer

    # Override read-only SerializerMethodField with writable field for input.
    attributes = JSONDictField(
        required=False, help_text="Dictionary of attributes to set."
    )

    cidr = fields.CharField(
        write_only=True,
        required=False,
        label="CIDR",
        help_text=(
            "IPv4/IPv6 CIDR address. If provided, this overrides the value of "
            "network_address & prefix_length. If not provided, "
            "network_address & prefix_length are required."
        ),
    )

    class Meta:
        model = models.Network
        fields = (
            "cidr",
            "network_address",
            "prefix_length",
            "attributes",
            "state",
            "site_id",
        )
        extra_kwargs = {
            "network_address": {"required": False},
            "prefix_length": {"required": False},
        }


class NetworkPartialUpdateSerializer(
    BulkSerializerMixin, NetworkCreateSerializer
):
    """Used for PATCH on Networks."""

    class Meta:
        model = models.Network
        list_serializer_class = BulkListSerializer
        fields = ("id", "attributes", "state")


class NetworkUpdateSerializer(NetworkPartialUpdateSerializer):
    """Used for PUT on Networks."""

    class Meta(NetworkPartialUpdateSerializer.Meta):
        extra_kwargs = {"attributes": {"required": True}}


###########
# Interface
###########
class InterfaceSerializer(ResourceSerializer):
    """Used for GET, DELETE on Interfaces."""

    parent_id = NaturalKeyRelatedField(
        required=False,
        allow_null=True,
        slug_field="name_slug",
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Interface, "parent", "verbose_name"),
        help_text=get_field_attr(models.Interface, "parent", "help_text"),
    )
    parent = serializers.SerializerMethodField(
        help_text="Natural key (slug) of the parent Interface, if any.",
    )
    device = NaturalKeyRelatedField(
        slug_field="hostname",
        queryset=models.Device.objects.all(),
        label=get_field_attr(models.Interface, "device", "verbose_name"),
        help_text=get_field_attr(models.Interface, "device", "help_text"),
    )
    device_hostname = serializers.CharField(
        read_only=True,
        help_text="Hostname of the device this Interface belongs to.",
    )
    addresses = serializers.SerializerMethodField(
        help_text="List of host addresses assigned to this Interface.",
    )
    networks = serializers.SerializerMethodField(
        help_text="List of parent networks derived from assigned addresses.",
    )
    mac_address = MACAddressField(
        required=False,
        allow_null=True,
        label=get_field_attr(models.Interface, "mac_address", "verbose_name"),
        help_text=get_field_attr(models.Interface, "mac_address", "help_text"),
    )
    type_name = serializers.SerializerMethodField(
        help_text="Human-readable name of the interface type.",
    )

    class Meta:
        model = models.Interface
        exclude = [
            "_attributes_cache",
            "_addresses_cache",
            "_networks_cache",
            "site",
        ]

    def get_parent(self, obj):
        return obj.parent.name_slug if obj.parent else None

    def get_addresses(self, obj):
        return obj.get_addresses()

    def get_networks(self, obj):
        return obj.get_networks()

    def get_type_name(self, obj):
        return obj.get_type_display()

    def validate_parent_id(self, value):
        """Cast the parent_id to an int if it's an Interface object."""
        # FIXME(jathan): Remove this hackery when we move away from `parent_id`
        # to `parent` in the future.
        if value is not None and isinstance(value, models.Interface):
            return value.id

        return value

    def create(self, validated_data):
        """Overload default create to handle setting of addresses."""
        log.debug(
            "InterfaceCreateSerializer.create() validated_data = %r",
            validated_data,
        )

        # Remove the related fields before we write the object
        addresses = validated_data.pop("addresses", [])

        # Create the base object to the database, but don't save attributes
        # yet.
        obj = super().create(validated_data, commit=False)

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_addresses(addresses)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
            obj.save()

        return obj

    def update(self, instance, validated_data):
        """Overload default update to handle setting of addresses."""
        log.debug(
            "InterfaceUpdateSerializer.update() validated_data = %r",
            validated_data,
        )

        # Remove related fields before we write the object. Attributes are
        # handled by the parent.
        addresses = validated_data.pop("addresses", None)

        # Update the attributes in the database, but don't save them yet.
        obj = super().update(instance, validated_data, commit=False)

        # Assign the address objects to the Interface.
        obj.set_addresses(addresses, overwrite=True, partial=self.partial)
        obj.save()

        return obj


class InterfaceTypeField(serializers.Field):
    """Accepts integer type IDs or string type names (e.g. 6 or "ethernet")."""

    default_error_messages = {
        "invalid": "Invalid interface type: {input!r}.",
    }

    def to_internal_value(self, data):
        from ..models import constants

        if data is None:
            return None
        if isinstance(data, str):
            # Try name lookup first (e.g. "ethernet" -> 6)
            resolved = constants.INTERFACE_TYPE_BY_NAME.get(data)
            if resolved is not None:
                return resolved
            # Try numeric string (e.g. "6" -> 6, common in form data)
            try:
                return int(data)
            except ValueError:
                self.fail("invalid", input=data)
        try:
            return int(data)
        except (TypeError, ValueError):
            self.fail("invalid", input=data)

    def to_representation(self, value):
        return value


class InterfaceCreateSerializer(WriteSerializerMixin, InterfaceSerializer):
    """Used for POST on Interfaces."""

    read_serializer_class = InterfaceSerializer

    # Override read-only SerializerMethodFields with writable fields.
    parent_id = NaturalKeyRelatedField(
        required=False,
        allow_null=True,
        slug_field="name_slug",
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Interface, "parent", "verbose_name"),
        help_text=get_field_attr(models.Interface, "parent", "help_text"),
    )
    addresses = JSONListField(
        required=False, help_text="List of host addresses to assign."
    )
    attributes = JSONDictField(
        required=False, help_text="Dictionary of attributes to set."
    )
    description = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=255
    )
    type = InterfaceTypeField(
        required=False,
        allow_null=True,
        default=settings.INTERFACE_DEFAULT_TYPE,
    )

    class Meta:
        model = models.Interface
        fields = (
            "device",
            "name",
            "description",
            "type",
            "mac_address",
            "speed",
            "mtu",
            "parent_id",
            "addresses",
            "attributes",
        )


class InterfacePartialUpdateSerializer(
    BulkSerializerMixin, InterfaceCreateSerializer
):
    "Used for PATCH on Interfaces."

    class Meta:
        model = models.Interface
        list_serializer_class = BulkListSerializer
        fields = (
            "id",
            "name",
            "description",
            "type",
            "mac_address",
            "speed",
            "mtu",
            "parent_id",
            "addresses",
            "attributes",
        )


class InterfaceUpdateSerializer(InterfacePartialUpdateSerializer):
    "Used for PUT on Interfaces."

    class Meta(InterfacePartialUpdateSerializer.Meta):
        extra_kwargs = {
            "addresses": {"required": True},
            "attributes": {"required": True},
        }


#########
# Circuit
#########
class CircuitSerializer(ResourceSerializer):
    """Used for GET, DELETE on Circuits"""

    endpoint_a = serializers.SerializerMethodField(
        help_text="Natural key (slug) of the A-side Interface.",
    )
    endpoint_z = serializers.SerializerMethodField(
        help_text="Natural key (slug) of the Z-side Interface.",
    )

    class Meta:
        model = models.Circuit
        exclude = ["_attributes_cache", "site"]

    def get_endpoint_a(self, obj):
        return obj.endpoint_a.name_slug if obj.endpoint_a else None

    def get_endpoint_z(self, obj):
        return obj.endpoint_z.name_slug if obj.endpoint_z else None


class CircuitCreateSerializer(WriteSerializerMixin, CircuitSerializer):
    """Used for POST on Circuits."""

    read_serializer_class = CircuitSerializer

    # Override read-only SerializerMethodFields with writable fields.
    endpoint_a = NaturalKeyRelatedField(
        slug_field="name_slug",
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Circuit, "endpoint_a", "verbose_name"),
        help_text=get_field_attr(models.Circuit, "endpoint_a", "help_text"),
    )
    endpoint_z = NaturalKeyRelatedField(
        slug_field="name_slug",
        required=False,
        allow_null=True,
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Circuit, "endpoint_z", "verbose_name"),
        help_text=get_field_attr(models.Circuit, "endpoint_z", "help_text"),
    )
    attributes = JSONDictField(
        required=False, help_text="Dictionary of attributes to set."
    )

    class Meta:
        model = models.Circuit
        # Display name is auto-generated, don't include it here.
        fields = ("site_id", "endpoint_a", "endpoint_z", "name", "attributes")


class CircuitPartialUpdateSerializer(
    BulkSerializerMixin, CircuitCreateSerializer
):
    """Used for PATCH on Circuits."""

    class Meta:
        model = models.Circuit
        list_serializer_class = BulkListSerializer
        fields = ("id", "endpoint_a", "endpoint_z", "name", "attributes")


class CircuitUpdateSerializer(CircuitPartialUpdateSerializer):
    """Used for PUT on Circuits."""

    class Meta(CircuitPartialUpdateSerializer.Meta):
        extra_kwargs = {"attributes": {"required": True}}


##############
# ProtocolType
##############
class ProtocolTypeSerializer(NsotSerializer):
    """Used for all CRUD operations on ProtocolTypes."""

    required_attributes = NaturalKeyRelatedField(
        many=True,
        slug_field="name",
        required=False,
        queryset=models.Attribute.objects.all(),
        help_text=get_field_attr(
            models.ProtocolType, "required_attributes", "help_text"
        ),
    )

    class Meta:
        model = models.ProtocolType
        fields = "__all__"


##########
# Protocol
##########
class ProtocolSerializer(ResourceSerializer):
    """Used for GET, DELETE on Protocols"""

    site = serializers.IntegerField(
        source="site_id",
        read_only=True,
        help_text="Unique ID of the Site this object is under.",
    )
    type = serializers.SerializerMethodField(
        help_text=get_field_attr(models.Protocol, "type", "help_text"),
    )
    device = serializers.SerializerMethodField(
        help_text=get_field_attr(models.Protocol, "device", "help_text"),
    )
    interface = serializers.SerializerMethodField(
        help_text=get_field_attr(models.Protocol, "interface", "help_text"),
    )
    circuit = serializers.SerializerMethodField(
        help_text=get_field_attr(models.Protocol, "circuit", "help_text"),
    )

    # Protocol's to_dict() uses "site" (not "site_id") as the key name, so we
    # suppress the inherited declared field from ResourceSerializer.  This is
    # the standard DRF mechanism for removing inherited declared fields.
    site_id = None

    class Meta:
        model = models.Protocol
        exclude = ["_attributes_cache"]

    def get_type(self, obj):
        return obj.type.name

    def get_device(self, obj):
        return obj.device.hostname

    def get_interface(self, obj):
        return obj.interface.name_slug if obj.interface else None

    def get_circuit(self, obj):
        return obj.circuit.name_slug if obj.circuit else None


class ProtocolCreateSerializer(WriteSerializerMixin, ProtocolSerializer):
    """Used for POST on Protocols."""

    read_serializer_class = ProtocolSerializer

    # Override read-only fields with writable fields for create/update.
    site = serializers.PrimaryKeyRelatedField(
        queryset=models.Site.objects.all(),
        help_text="Unique ID of the Site this object is under.",
        label="Site",
    )
    type = NaturalKeyRelatedField(
        slug_field="name",
        queryset=models.ProtocolType.objects.all(),
        help_text=get_field_attr(models.Protocol, "type", "help_text"),
    )
    device = NaturalKeyRelatedField(
        slug_field="hostname",
        queryset=models.Device.objects.all(),
        help_text=get_field_attr(models.Protocol, "device", "help_text"),
    )
    interface = NaturalKeyRelatedField(
        slug_field="name_slug",
        required=False,
        allow_null=True,
        queryset=models.Interface.objects.all(),
        help_text=get_field_attr(models.Protocol, "interface", "help_text"),
    )
    circuit = NaturalKeyRelatedField(
        slug_field="name_slug",
        required=False,
        allow_null=True,
        queryset=models.Circuit.objects.all(),
        help_text=get_field_attr(models.Protocol, "circuit", "help_text"),
    )
    attributes = JSONDictField(
        required=False, help_text="Dictionary of attributes to set."
    )

    class Meta:
        model = models.Protocol
        fields = (
            "site",
            "type",
            "device",
            "description",
            "auth_string",
            "interface",
            "circuit",
            "attributes",
        )


class ProtocolPartialUpdateSerializer(
    BulkSerializerMixin, ProtocolCreateSerializer
):
    """Used for PATCH on Protocols."""

    class Meta:
        model = models.Protocol
        list_serializer_class = BulkListSerializer
        fields = (
            "id",
            "site",
            "type",
            "device",
            "description",
            "auth_string",
            "interface",
            "circuit",
            "attributes",
        )


class ProtocolUpdateSerializer(ProtocolPartialUpdateSerializer):
    """Used for PUT on Protocols."""

    class Meta(ProtocolPartialUpdateSerializer.Meta):
        extra_kwargs = {"attributes": {"required": True}}


###########
# AuthToken
###########
class AuthTokenSerializer(serializers.Serializer):
    """
    AuthToken authentication serializer to validate username/secret_key inputs.
    """

    email = serializers.CharField(help_text="Email address of the user.")
    secret_key = serializers.CharField(
        label="Secret Key", help_text="Secret key of the user."
    )

    def validate(self, attrs):
        email = attrs.get("email")
        secret_key = attrs.get("secret_key")

        if email and secret_key:
            auth_func = auth.SecretKeyAuthentication().authenticate_credentials
            user, secret_key = auth_func(email, secret_key)

            if user:
                if not user.is_active:
                    msg = "User account is disabled."
                    raise exc.ValidationError(msg)
                attrs["user"] = user
                return attrs
            msg = "Unable to login with provided credentials."
            raise exc.ValidationError(msg)
        msg = 'Must include "email" and "secret_key"'
        raise exc.ValidationError(msg)
