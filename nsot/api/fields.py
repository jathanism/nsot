from __future__ import unicode_literals
import ast
import json
import logging

from rest_framework import fields, serializers

from .. import exc, validators


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
        log.debug('JSONDictField.to_internal_value() data = %r', data)
        if self.field_type is None:
            raise NotImplementedError(
                'You must subclass JSONDataField and define field_type'
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


class MACAddressField(fields.Field):
    """Field used to validate MAC address objects as integer or string."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, value):
        return validators.validate_mac_address(value)


class NaturalKeyRelatedField(serializers.SlugRelatedField):
    """Field that takes either a primary key or a natural key."""
    def to_representation(self, value):
        return value

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
                'NaturalKeyRelatedField: %s using PK field for value %s',
                self.field_name, value
            )
        # Or it's natural key. Brute force!!
        else:
            field = serializers.SlugRelatedField(
                slug_field=self.slug_field,
                queryset=self.get_queryset(),
            )
            log.debug(
                'NaturalKeyRelatedField: %s using SLUG field for value %s',
                self.field_name, value
            )

        value = field.to_internal_value(value)

        return value

    def get_queryset(self):
        """Filter eligible related objects to the current site."""
        queryset = super(NaturalKeyRelatedField, self).get_queryset()
        request = self.context.get('request')

        if request is None:
            data = {}
        else:
            is_bulk = isinstance(request.data, list)
            if is_bulk:
                data = request.data[0]
            else:
                data = request.data

        site_id = data.get('site_id')

        if site_id is not None:
            log.debug('Filtering queryset to site_id=%s', site_id)
            queryset = queryset.filter(site_id=site_id)

        return queryset
