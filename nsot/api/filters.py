import logging

import django_filters
from django.db.models import Q

from .. import models
from ..util import qpbool

log = logging.getLogger(__name__)


class ChangeFilter(django_filters.rest_framework.FilterSet):
    """Filter for Change objects."""

    user = django_filters.NumberFilter(field_name="user")
    change_at__gte = django_filters.IsoDateTimeFilter(
        field_name="change_at", lookup_expr="gte"
    )
    change_at__lte = django_filters.IsoDateTimeFilter(
        field_name="change_at", lookup_expr="lte"
    )

    class Meta:
        model = models.Change
        fields = [
            "event",
            "resource_name",
            "resource_id",
            "user",
            "change_at__gte",
            "change_at__lte",
        ]


class AttributeFilter(django_filters.rest_framework.FilterSet):
    required = django_filters.BooleanFilter()
    display = django_filters.BooleanFilter()
    multi = django_filters.BooleanFilter()
    has_dependencies = django_filters.BooleanFilter(
        method="filter_has_dependencies",
        help_text="Filter attributes that have dependencies (true) or don't (false).",
    )

    def filter_has_dependencies(self, queryset, name, value):
        if value:
            return queryset.filter(depends_on__isnull=False).distinct()
        return queryset.filter(depends_on__isnull=True)

    class Meta:
        model = models.Attribute
        fields = ["name", "resource_name", "required", "display", "multi"]


class ResourceFilter(django_filters.rest_framework.FilterSet):
    """Attribute-aware filtering for Resource objects."""

    attributes = django_filters.CharFilter(method="filter_attributes")
    expired = django_filters.BooleanFilter(
        method="filter_expired",
        help_text="Filter by expiration status (true=expired, false=not expired).",
    )
    expires_before = django_filters.IsoDateTimeFilter(
        field_name="expires_at",
        lookup_expr="lte",
        help_text="Resources expiring on or before this ISO timestamp.",
    )
    expires_after = django_filters.IsoDateTimeFilter(
        field_name="expires_at",
        lookup_expr="gte",
        help_text="Resources expiring on or after this ISO timestamp.",
    )

    def filter_expired(self, queryset, name, value):
        """Delegate to the queryset's ``.expired()`` method."""
        return queryset.expired(expired=value)

    def filter_attributes(self, queryset, name, value):
        """
        Reads 'attributes' from query params and joins them together as an
        intersection set query.

        When an attribute is marked as ``inheritable``, resources that inherit
        the value from an ancestor (i.e. they don't have their own explicit
        value but an ancestor does) are included in the results.
        """
        attributes = self.data.getlist("attributes", [])
        resource_name = queryset.model.__name__

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        log.debug("GOT ATTRIBUTES: %r", attributes)

        for attribute in attributes:
            attr_name, _, attr_value = attribute.partition("=")

            # Retrieve next set of objects with explicit matches.
            explicit_ids = set(
                models.Value.objects.filter(
                    name=attr_name,
                    value=attr_value,
                    resource_name=resource_name,
                ).values_list("resource_id", flat=True)
            )

            matching_ids = set(explicit_ids)

            # Check if this attribute is inheritable and expand to descendants.
            try:
                # Derive site from the queryset (all resources share a site).
                site_id = None
                view = getattr(self, "request", None)
                if view is None:
                    view = self.data.get("site_pk") or self.data.get("site_id")
                    if view:
                        site_id = int(view)
                if site_id is None:
                    # Try from view kwargs
                    request = getattr(self, "request", None)
                    if request:
                        view_obj = getattr(request, "parser_context", {}).get(
                            "view"
                        )
                        if view_obj:
                            site_id = view_obj.kwargs.get("site_pk")
                if site_id is None:
                    # Last resort: peek at queryset
                    first = queryset.first()
                    if first:
                        site_id = first.site_id

                if site_id is not None:
                    attr_obj = models.Attribute.objects.filter(
                        name=attr_name,
                        resource_name=resource_name,
                        site_id=site_id,
                        inheritable=True,
                    ).first()

                    if attr_obj is not None and hasattr(
                        queryset.model, "get_descendants"
                    ):
                        # For each explicit match, get its descendants.
                        explicit_resources = queryset.model.objects.filter(
                            id__in=explicit_ids
                        )
                        descendant_ids = set()
                        for resource in explicit_resources:
                            descendant_ids.update(
                                resource.get_descendants().values_list(
                                    "id", flat=True
                                )
                            )

                        # Exclude descendants that have their own explicit
                        # value for this attribute (they override).
                        overrider_ids = set(
                            models.Value.objects.filter(
                                name=attr_name,
                                resource_name=resource_name,
                                resource_id__in=descendant_ids,
                            )
                            .exclude(value=attr_value)
                            .values_list("resource_id", flat=True)
                        )

                        # Recursively exclude the entire subtree below
                        # each overrider, since those descendants inherit
                        # the overrider's value, not the original.
                        overrider_subtree_ids = set()
                        overrider_resources = queryset.model.objects.filter(
                            id__in=overrider_ids
                        )
                        for overrider in overrider_resources:
                            overrider_subtree_ids.update(
                                overrider.get_descendants().values_list(
                                    "id", flat=True
                                )
                            )

                        # Also exclude descendants that have the SAME value
                        # explicitly — they're already in explicit_ids or
                        # should be included anyway.
                        matching_ids = explicit_ids | (
                            descendant_ids
                            - overrider_ids
                            - overrider_subtree_ids
                        )
            except (models.Attribute.DoesNotExist, ValueError, TypeError):
                log.warning(
                    "Inheritance expansion failed for %r, using explicit only",
                    attr_name,
                    exc_info=True,
                )

            next_set = Q(id__in=matching_ids)
            queryset = queryset.filter(next_set)

        return queryset


class DeviceFilter(ResourceFilter):
    """Filter for Device objects."""

    class Meta:
        model = models.Device
        fields = [
            "hostname",
            "attributes",
            "expired",
            "expires_before",
            "expires_after",
        ]


class NetworkFilter(ResourceFilter):
    """Filter for Network objects."""

    include_networks = django_filters.BooleanFilter(
        method="filter_include_networks"
    )
    include_ips = django_filters.BooleanFilter(method="filter_include_ips")
    cidr = django_filters.CharFilter(method="filter_cidr")
    root_only = django_filters.BooleanFilter(method="filter_root_only")
    network_address = django_filters.CharFilter()  # Override type

    class Meta:
        model = models.Network
        fields = [
            "include_networks",
            "include_ips",
            "root_only",
            "cidr",
            "network_address",
            "prefix_length",
            "ip_version",
            "state",
            "attributes",
            "expired",
            "expires_before",
            "expires_after",
        ]

    def filter_include_networks(self, queryset, name, value):
        """Converts ``include_networks`` to queryset filters."""
        include_ips = qpbool(self.form.cleaned_data["include_ips"])
        include_networks = qpbool(value)

        if not all([include_networks, include_ips]):
            if include_networks:
                return queryset.filter(is_ip=False)
            return queryset.exclude(is_ip=False)

        return queryset

    def filter_include_ips(self, queryset, name, value):
        """Converts ``include_ips`` to queryset filters."""
        include_ips = qpbool(value)
        include_networks = qpbool(self.form.cleaned_data["include_networks"])

        if not all([include_networks, include_ips]):
            if include_ips:
                return queryset.filter(is_ip=True)
            return queryset.exclude(is_ip=True)

        return queryset

    def filter_cidr(self, queryset, name, value):
        """Converts ``cidr`` to network/prefix filter."""
        if value:
            network_address, _, prefix_length = value.partition("/")
        else:
            return queryset

        return queryset.filter(
            network_address=network_address, prefix_length=prefix_length
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

    mac_address = django_filters.CharFilter(method="filter_mac_address")

    class Meta:
        model = models.Interface
        # TODO: Remove `device__hostname` in a future release after
        #       updating pynsot to use `device_hostname`.
        fields = [
            "device",
            "device__hostname",
            "name",
            "speed",
            "mtu",
            "type",
            "mac_address",
            "description",
            "parent_id",
            "attributes",
            "device_hostname",
            "expired",
            "expires_before",
            "expires_after",
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

    endpoint_a = django_filters.CharFilter(method="filter_endpoint_a")
    endpoint_z = django_filters.CharFilter(method="filter_endpoint_z")
    device_hostname = django_filters.CharFilter(
        method="filter_device_hostname"
    )

    class Meta:
        model = models.Circuit
        fields = [
            "endpoint_a",
            "endpoint_z",
            "name",
            "device_hostname",
            "attributes",
            "expired",
            "expires_before",
            "expires_after",
        ]

    # FIXME(jathan): The copy/pasted methods can be ripped out once we upgrade
    # filters in support of the V2 API. For now this is quicker and easier.
    def filter_endpoint_a(self, queryset, name, value):
        """Overload to use natural key."""
        if isinstance(value, int):
            value = str(value)

        if value.isdigit():
            return queryset.filter(endpoint_a=value)
        return queryset.filter(endpoint_a__name_slug=value)

    def filter_endpoint_z(self, queryset, name, value):
        """Overload to use natural key."""
        if isinstance(value, int):
            value = str(value)

        if value.isdigit():
            return queryset.filter(endpoint_z=value)
        return queryset.filter(endpoint_z__name_slug=value)

    def filter_device_hostname(self, queryset, name, value):
        """Filter circuits by device hostname on either endpoint."""
        return queryset.filter(
            Q(endpoint_a__device__hostname=value)
            | Q(endpoint_z__device__hostname=value)
        )


class ProtocolTypeFilter(django_filters.rest_framework.FilterSet):
    """Filter for ProtocolType (non-resource) objects."""

    class Meta:
        model = models.ProtocolType
        fields = ["name", "description"]


class ProtocolFilter(ResourceFilter):
    """Filter for Protocol objects."""

    device = django_filters.CharFilter(method="filter_device")
    type = django_filters.CharFilter(method="filter_type")
    interface = django_filters.CharFilter(method="filter_interface")
    circuit = django_filters.CharFilter(method="filter_circuit")

    class Meta:
        model = models.Protocol
        fields = [
            "device",
            "type",
            "interface",
            "circuit",
            "description",
            "expired",
            "expires_before",
            "expires_after",
        ]

    def filter_device(self, queryset, name, value):
        """Overload to use natural key."""
        if isinstance(value, int):
            value = str(value)

        if value.isdigit():
            return queryset.filter(device=value)
        return queryset.filter(device__hostname=value)

    def filter_type(self, queryset, name, value):
        """Overload to use natural key."""
        if isinstance(value, int):
            value = str(value)

        if value.isdigit():
            return queryset.filter(type=value)
        return queryset.filter(type__name=value)

    def filter_interface(self, queryset, name, value):
        """Overload to use natural key."""
        if isinstance(value, int):
            value = str(value)

        if value.isdigit():
            return queryset.filter(interface=value)
        return queryset.filter(interface__name_slug=value)

    def filter_circuit(self, queryset, name, value):
        """Overload to use natural key."""
        if isinstance(value, int):
            value = str(value)

        if value.isdigit():
            return queryset.filter(circuit=value)
        return queryset.filter(circuit__name_slug=value)
