# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import coreschema
from django.utils.encoding import force_text
from rest_framework import schemas
from rest_framework_bulk.routes import BulkRouter as BulkRouterBase
from rest_framework_nested.routers import NestedSimpleRouter


__all__ = ('BulkRouter', 'BulkNestedRouter')


# Map of HTTP verbs to rest_framework_bulk operations.
BULK_OPERATIONS_MAP = {
    'put': 'bulk_update',
    'patch': 'partial_bulk_update',
    'delete': 'bulk_destroy',
}

# FIXME(jathan): This entire concept of coercing field schema can go away once
# we've replaced all serializer fields w/ the correct types.
FIELD_FIXUPS = {
    'constraints': 'object',
    'attributes': 'object',
    'addresses': 'array',
}

SCHEMA_TYPE_MAP = {
    'array': coreschema.Array,
    'object': coreschema.Object,
}


def coerce_field_schema(field, field_type):
    """Given a field and a type, return a new field w/ that type set."""
    schema_type = SCHEMA_TYPE_MAP.get(field_type)

    if schema_type is None:
        return field

    old_schema = field.schema
    new_schema = schema_type(
        title=old_schema.title,
        description=old_schema.description,
    )

    return field._replace(schema=new_schema)


class NsotSchemaGenerator(schemas.SchemaGenerator):
    """
    Schema generator that will coerce specified fields to the desired type.
    """
    def get_serializer_fields(self, path, method, view):
        fields = super(NsotSchemaGenerator, self).get_serializer_fields(
            path, method, view
        )

        if fields:
            self.coerce_field_schemas(fields)

        return fields

    def coerce_field_schemas(self, fields):
        fields_map = {f.name: f for f in fields}

        for field_name, field_type in FIELD_FIXUPS.iteritems():
            if field_name in fields_map:
                field = fields_map[field_name]
                field_index = fields.index(field)
                new_field = coerce_field_schema(field, field_type)
                fields[field_index] = new_field  # Replace the field


class NsotRouterMixin(object):
    SchemaGenerator = NsotSchemaGenerator


class BulkRouter(NsotRouterMixin, BulkRouterBase):
    pass


class BulkNestedRouter(NsotRouterMixin, NestedSimpleRouter):
    """
    Bulk-enabled nested router.
    """
    def __init__(self, *args, **kwargs):
        super(BulkNestedRouter, self).__init__(*args, **kwargs)
        self.routes[0].mapping.update(BULK_OPERATIONS_MAP)
