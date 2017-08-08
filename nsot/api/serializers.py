from __future__ import unicode_literals
from collections import OrderedDict
import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer

from . import auth, fields
from .. import exc, models
from ..util import get_field_attr


log = logging.getLogger(__name__)


###################
# Base Serializer #
###################
class NsotSerializer(serializers.ModelSerializer):
    """Base serializer that logs change events."""
    def to_internal_value(self, data):
        """Inject site_pk from view's kwargs if it's not already in data."""
        # Try to get the kwargs from the view, or default to empty kwargs.
        view = self.context.get('view')
        kwargs = getattr(view, 'kwargs', {})

        log.debug(
            'NsotSerializer.to_internal_value() data [before] = %r', data
        )

        if 'site_id' not in data and 'site_pk' in kwargs:
            data['site_id'] = kwargs['site_pk']

        log.debug('NsotSerializer.to_internal_value() data [after] = %r', data)

        return super(NsotSerializer, self).to_internal_value(data)

    def to_representation(self, obj):
        """Always return the dict representation."""
        if isinstance(obj, OrderedDict):
            return obj
        return obj.to_dict()


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
        self.with_secret_key = kwargs.pop('with_secret_key', None)
        super(UserSerializer, self).__init__(*args, **kwargs)

        # If we haven't passed `with_secret_key`, don't show the secret_key
        # field.
        if self.with_secret_key is None:
            self.fields.pop('secret_key')

    permissions = serializers.ReadOnlyField(source='get_permissions')

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'permissions', 'secret_key')


######
# Site
######
class SiteSerializer(serializers.ModelSerializer):
    """Used for all Site operations."""
    class Meta:
        model = models.Site
        fields = '__all__'


#########
# Changes
#########
class ChangeSerializer(NsotSerializer):
    """Used for displaying Change events."""
    class Meta:
        model = models.Change
        fields = '__all__'


###########
# Attribute
###########
class AttributeSerializer(NsotSerializer):
    """Used for GET, DELETE on Attributes."""
    class Meta:
        model = models.Attribute
        fields = '__all__'


class AttributeCreateSerializer(AttributeSerializer):
    """Used for POST on Attributes."""
    constraints = fields.JSONDictField(
        required=False,
        label=get_field_attr(models.Attribute, 'constraints', 'verbose_name'),
        help_text=get_field_attr(models.Attribute, 'constraints', 'help_text')
    )
    site_id = serializers.IntegerField(
        label=get_field_attr(models.Attribute, 'site', 'verbose_name'),
        help_text=get_field_attr(models.Attribute, 'site', 'help_text')
    )

    class Meta:
        model = models.Attribute
        fields = ('name', 'description', 'resource_name', 'required',
                  'display', 'multi', 'constraints', 'site_id')


class AttributeUpdateSerializer(BulkSerializerMixin,
                                AttributeCreateSerializer):
    """
    Used for PUT, PATCH, on Attributes.

    Currently because Attributes have only one required field (name), and it
    may not be updated, there is not much functional difference between PUT and
    PATCH.
    """
    class Meta:
        model = models.Attribute
        list_serializer_class = BulkListSerializer
        fields = ('id', 'description', 'required', 'display', 'multi',
                  'constraints')


#######
# Value
#######
class ValueSerializer(serializers.ModelSerializer):
    """Used for GET, DELETE on Values."""
    class Meta:
        model = models.Value
        fields = ('id', 'name', 'value', 'attribute', 'resource_name',
                  'resource_id')


class ValueCreateSerializer(ValueSerializer):
    """Used for POST on Values."""
    class Meta(ValueSerializer.Meta):
        read_only_fields = ('id', 'name', 'resource_name')


###########
# Resources
###########
class ResourceSerializer(NsotSerializer):
    """For any object that can have attributes."""
    # attributes = fields.JSONDictField(
    #     required=False,
    attributes = serializers.JSONField(
        binary=False,
        required=False,
        help_text='Dictionary of attributes to set.'
    )
    site_id = serializers.PrimaryKeyRelatedField(
        source='site', queryset=models.Site.objects.all(),
        help_text='Unique ID of the Site this object is under.',
        label='Site',
    )

    def create(self, validated_data, commit=True):
        """Create that is aware of attributes."""
        # Remove the related fields before we write the object
        attributes = validated_data.pop('attributes', {})

        # Save the base object to the database.
        obj = super(ResourceSerializer, self).create(validated_data)

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
        attributes = validated_data.pop('attributes', None)

        # Save the object to the database.
        obj = super(ResourceSerializer, self).update(
            instance, validated_data
        )

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
        fields = '__all__'


class DeviceCreateSerializer(DeviceSerializer):
    """Used for POST on Devices."""

    class Meta:
        model = models.Device
        fields = ('hostname', 'attributes', 'site_id')


class DevicePartialUpdateSerializer(BulkSerializerMixin,
                                    DeviceCreateSerializer):
    """Used for PATCH on Devices."""
    class Meta:
        model = models.Device
        list_serializer_class = BulkListSerializer
        fields = ('id', 'hostname', 'attributes')


class DeviceUpdateSerializer(DevicePartialUpdateSerializer):
    """Used for PUT on Devices."""

    class Meta(DevicePartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


#########
# Network
#########
class NetworkSerializer(ResourceSerializer):
    """Used for GET, DELETE on Networks."""

    class Meta:
        model = models.Network
        fields = '__all__'


class NetworkCreateSerializer(NetworkSerializer):
    """Used for POST on Networks."""
    cidr = serializers.CharField(
        write_only=True, required=False, label='CIDR',
        help_text=(
            'IPv4/IPv6 CIDR address. If provided, this overrides the value of '
            'network_address & prefix_length. If not provided, '
            'network_address & prefix_length are required.'
        )
    )

    class Meta:
        model = models.Network
        fields = ('cidr', 'network_address', 'prefix_length', 'attributes',
                  'state', 'site_id')
        extra_kwargs = {
            'network_address': {'required': False},
            'prefix_length': {'required': False},
        }


class NetworkPartialUpdateSerializer(BulkSerializerMixin,
                                     NetworkCreateSerializer):
    """Used for PATCH on Networks."""

    class Meta:
        model = models.Network
        list_serializer_class = BulkListSerializer
        fields = ('id', 'attributes', 'state')


class NetworkUpdateSerializer(NetworkPartialUpdateSerializer):
    """Used for PUT on Networks."""

    class Meta(NetworkPartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


class AddressSerializer(serializers.Serializer):
    address = serializers.CharField()

    def validate_address(self, value):
        from nsot import validators
        return validators.validate_host_address(value)

    def to_representation(self, value):
        if value:
            return value['address']
        return value


###########
# Interface
###########
class InterfaceSerializer(ResourceSerializer):
    """Used for GET, DELETE on Interfaces."""
    parent_id = fields.NaturalKeyRelatedField(
        required=False, allow_null=True,
        slug_field='name_slug',
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Interface, 'parent', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'parent', 'help_text'),
    )
    device = fields.NaturalKeyRelatedField(
        slug_field='hostname',
        queryset=models.Device.objects.all(),
        label=get_field_attr(models.Interface, 'device', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'device', 'help_text'),
    )
    # addresses = fields.JSONListField(
    addresses = serializers.ListField(
        child=serializers.CharField(),
        required=False, help_text='List of host addresses to assign.'
    )
    mac_address = fields.MACAddressField(
        required=False, allow_null=True,
        label=get_field_attr(models.Interface, 'mac_address', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'mac_address', 'help_text'),
    )

    class Meta:
        model = models.Interface
        fields = '__all__'

    def validate_parent_id(self, value):
        """Cast the parent_id to an int if it's an Interface object."""
        # FIXME(jathan): Remove this hackery when we move away from `parent_id`
        # to `parent` in the future.
        if value is not None and isinstance(value, models.Interface):
            return value.id

        return value

    def create(self, validated_data):
        """Overload default create to handle setting of addresses."""
        log.debug('InterfaceCreateSerializer.create() validated_data = %r',
                  validated_data)

        # Remove the related fields before we write the object
        addresses = validated_data.pop('addresses', [])

        # Create the base object to the database, but don't save attributes
        # yet.
        obj = super(InterfaceSerializer, self).create(
            validated_data, commit=False
        )

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
        log.debug('InterfaceUpdateSerializer.update() validated_data = %r',
                  validated_data)

        # Remove related fields before we write the object. Attributes are
        # handled by the parent.
        addresses = validated_data.pop('addresses', None)

        # Update the attributes in the database, but don't save them yet.
        obj = super(InterfaceSerializer, self).update(
            instance, validated_data, commit=False
        )

        # Assign the address objects to the Interface.
        obj.set_addresses(addresses, overwrite=True, partial=self.partial)
        obj.save()

        return obj


class InterfaceCreateSerializer(InterfaceSerializer):
    """Used for POST on Interfaces."""

    class Meta:
        model = models.Interface
        fields = ('device', 'name', 'description', 'type', 'mac_address',
                  'speed', 'parent_id', 'addresses', 'attributes')


class InterfacePartialUpdateSerializer(BulkSerializerMixin,
                                       InterfaceCreateSerializer):
    "Used for PATCH on Interfaces."""
    class Meta:
        model = models.Interface
        list_serializer_class = BulkListSerializer
        fields = ('id', 'name', 'description', 'type', 'mac_address', 'speed',
                  'parent_id', 'addresses', 'attributes')


class InterfaceUpdateSerializer(InterfacePartialUpdateSerializer):
    "Used for PUT on Interfaces."""

    class Meta(InterfacePartialUpdateSerializer.Meta):
        extra_kwargs = {
            'addresses': {'required': True},
            'attributes': {'required': True},
        }


#########
# Circuit
#########
class CircuitSerializer(ResourceSerializer):
    """Used for GET, DELETE on Circuits"""
    endpoint_a = fields.NaturalKeyRelatedField(
        slug_field='name_slug',
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Circuit, 'endpoint_a', 'verbose_name'),
        help_text=get_field_attr(models.Circuit, 'endpoint_a', 'help_text'),
    )
    endpoint_z = fields.NaturalKeyRelatedField(
        slug_field='name_slug',
        required=False, allow_null=True,
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Circuit, 'endpoint_z', 'verbose_name'),
        help_text=get_field_attr(models.Circuit, 'endpoint_z', 'help_text'),
    )

    class Meta:
        model = models.Circuit
        fields = '__all__'


class CircuitCreateSerializer(CircuitSerializer):
    """Used for POST on Circuits."""

    class Meta:
        model = models.Circuit
        # Display name and site are auto-generated, don't include them here.
        fields = ('endpoint_a', 'endpoint_z', 'name', 'attributes')


class CircuitPartialUpdateSerializer(BulkSerializerMixin,
                                     CircuitCreateSerializer):
    """Used for PATCH on Circuits."""
    class Meta:
        model = models.Circuit
        list_serializer_class = BulkListSerializer
        fields = ('id', 'endpoint_a', 'endpoint_z', 'name', 'attributes')


class CircuitUpdateSerializer(CircuitPartialUpdateSerializer):
    """Used for PUT on Circuits."""

    class Meta(CircuitPartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


###########
# AuthToken
###########
class AuthTokenSerializer(serializers.Serializer):
    """
    AuthToken authentication serializer to validate username/secret_key inputs.
    """
    email = serializers.CharField(help_text='Email address of the user.')
    secret_key = serializers.CharField(
        label='Secret Key', help_text='Secret key of the user.'
    )

    def validate(self, attrs):
        email = attrs.get('email')
        secret_key = attrs.get('secret_key')

        if email and secret_key:
            auth_func = auth.SecretKeyAuthentication().authenticate_credentials
            user, secret_key = auth_func(email, secret_key)

            if user:
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise exc.ValidationError(msg)
                attrs['user'] = user
                return attrs
            else:
                msg = 'Unable to login with provided credentials.'
                raise exc.ValidationError(msg)
        else:
            msg = 'Must include "email" and "secret_key"'
            raise exc.ValidationError(msg)
