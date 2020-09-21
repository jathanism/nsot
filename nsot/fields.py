# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.conf import settings
from django.db import models
from django.utils.datastructures import DictWrapper
from django_extensions.db.fields.json import JSONField
from macaddress.fields import MACAddressField as BaseMACAddressField
import ipaddress
import logging
import six

from . import exc


__all__ = ("BinaryIPAddressField", "JSONField", "MACAddressField")


log = logging.getLogger(__name__)


class BinaryIPAddressField(models.Field):
    """IP Address field that stores values as varbinary."""

    def __init__(self, *args, **kwargs):
        super(BinaryIPAddressField, self).__init__(*args, **kwargs)
        self.editable = True

    def db_type(self, connection):
        engine = connection.settings_dict["ENGINE"]

        # Use the native 'inet' type for Postgres.
        if "postgres" in engine:
            return "inet"

        # Or 'varbinary' for everyone else.
        data = DictWrapper(self.__dict__, connection.ops.quote_name, "qn_")
        return "varbinary(%(max_length)s)" % data

    def _parse_ip_address(self, value):
        try:
            obj = ipaddress.ip_address(six.text_type(value))
        except ValueError:
            obj = ipaddress.ip_address(bytes(value))

        # Display IPv6 as compressed or not? This is a no-op vor IPv4.
        if settings.NSOT_COMPRESS_IPV6:
            return obj.compressed

        return obj.exploded

    def from_db_value(self, value, expression, connection):
        """DB -> Python."""
        if value is None:
            return value

        return self._parse_ip_address(value)

    def to_python(self, value):
        """Object -> Python."""
        if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return value

        if value is None:
            return value

        return self._parse_ip_address(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        """Python -> DB."""
        # To account for null defaults when performing migrations
        if value is None:
            return None

        engine = connection.settings_dict["ENGINE"]

        # Send the value as-is to Postgres.
        if "postgres" in engine:
            return value

        # Or packed binary for everyone else.
        return ipaddress.ip_address(value).packed


class MACAddressField(BaseMACAddressField):
    """
    Subclass of base field to raise a DRF ValidationError.

    DRF handles Django's default ValidationError, but this is so that we can
    always expect the DRF version, for better consistency in debugging and
    testing.
    """

    def from_db_value(self, value, expression, connection):
        # If value is an integer that is a string, make it an int
        if isinstance(value, six.string_types) and value.isdigit():
            value = int(value)

        try:
            return super(MACAddressField, self).from_db_value(
                value, expression, connection
            )
        except exc.DjangoValidationError as err:
            raise exc.ValidationError(str(err))

    def to_python(self, value):
        # If value is an integer that is a string, make it an int
        if isinstance(value, six.string_types) and value.isdigit():
            value = int(value)

        try:
            return super(MACAddressField, self).to_python(value)
        except exc.DjangoValidationError as err:
            raise exc.ValidationError(str(err))
