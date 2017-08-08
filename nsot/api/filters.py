from __future__ import unicode_literals
import logging

from django.db.models import Q
import django_filters

from .. import fields as api_fields, models
from ..util import qpbool


log = logging.getLogger(__name__)


class ResourceFilter(django_filters.rest_framework.FilterSet):
    """Attribute-aware filtering for Resource objects."""
    attributes = django_filters.CharFilter(method='filter_attributes')

    def filter_attributes(self, queryset, name, value):
        """
        Reads 'attributes' from query params and joins them together as an
        intersection set query.
        """
        attributes = self.data.getlist('attributes', [])
        resource_name = queryset.model.__name__

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        log.debug('GOT ATTRIBUTES: %r', attributes)

        for attribute in attributes:
            name, _, value = attribute.partition('=')
            # Retrieve next set of objects using the same arguments as the
            # initial query.
            next_set = Q(
                id__in=models.Value.objects.filter(
                    name=name, value=value, resource_name=resource_name
                ).values_list('resource_id', flat=True)
            )
            queryset = queryset.filter(next_set)

        return queryset


class DeviceFilter(ResourceFilter):
    """Filter for Device objects."""
    class Meta:
        model = models.Device
        fields = ['hostname', 'attributes']


class NetworkFilter(ResourceFilter):
    """Filter for Network objects."""
    include_networks = django_filters.BooleanFilter(
        method='filter_include_networks'
    )
    include_ips = django_filters.BooleanFilter(method='filter_include_ips')
    cidr = django_filters.CharFilter(method='filter_cidr')
    root_only = django_filters.BooleanFilter(method='filter_root_only')
    network_address = django_filters.CharFilter()  # Override type

    class Meta:
        model = models.Network
        fields = [
            'include_networks', 'include_ips', 'root_only', 'cidr',
            'network_address', 'prefix_length', 'ip_version', 'state',
            'attributes'
        ]

    def filter_include_networks(self, queryset, name, value):
        """Converts ``include_networks`` to queryset filters."""
        include_ips = qpbool(self.form.cleaned_data['include_ips'])
        include_networks = qpbool(value)

        if not all([include_networks, include_ips]):
            if include_networks:
                return queryset.filter(is_ip=False)
            else:
                return queryset.exclude(is_ip=False)

        return queryset

    def filter_include_ips(self, queryset, name, value):
        """Converts ``include_ips`` to queryset filters."""
        include_ips = qpbool(value)
        include_networks = qpbool(self.form.cleaned_data['include_networks'])

        if not all([include_networks, include_ips]):
            if include_ips:
                return queryset.filter(is_ip=True)
            else:
                return queryset.exclude(is_ip=True)

        return queryset

    def filter_cidr(self, queryset, name, value):
        """Converts ``cidr`` to network/prefix filter."""
        if value:
            network_address, _, prefix_length = value.partition('/')
        else:
            return queryset

        return queryset.filter(
            network_address=network_address,
            prefix_length=prefix_length
        )

    def filter_root_only(self, queryset, name, value):
        """Converts ``root_only`` to null parent filter."""
        if qpbool(value):
            return queryset.filter(parent=None)
        return queryset


class InterfaceFilter(ResourceFilter):
    """
    Filter for Interface objects.

    Includes a custom override for filtering on mac_address because this is not
    a Django built-in field.
    """
    mac_address = django_filters.CharFilter(method='filter_mac_address')

    class Meta:
        model = models.Interface
        # TODO: Remove `device__hostname` in a future release after
        #       updating pynsot to use `device_hostname`.
        fields = [
            'device', 'device__hostname', 'name', 'speed', 'type',
            'mac_address', 'description', 'parent_id', 'attributes',
            'device_hostname'
        ]

    def filter_mac_address(self, queryset, name, value):
        """
        Overloads queryset filtering to use built-in.

        Doesn't work by default because MACAddressField is not a Django
        built-in field type.
        """
        return queryset.filter(mac_address=value)


class CircuitFilter(ResourceFilter):
    """Filter for Circuit objects."""
    class Meta:
        model = models.Circuit
        fields = ['endpoint_a', 'endpoint_z', 'name', 'attributes']
