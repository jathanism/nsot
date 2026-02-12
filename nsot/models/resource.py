import logging

from django.db import models
from django.db.models.query_utils import Q

from .. import exc, fields, util
from .attribute import Attribute
from .value import Value

log = logging.getLogger(__name__)


class ResourceSetTheoryQuerySet(models.query.QuerySet):
    """
    Set theory QuerySet for Resource objects to add ``.set_query()`` method.

    For example::

        >>> qs = Network.objects.filter(network_address=u'10.0.0.0')
        >>> qs.set_query('owner=jathan +metro=lax')

    You may also search using regex by appending ``_regex`` to an attribtue
    name and providing a regex pattern as the value::

        >>> qs = Device.objects.set_query('role_regex=[bd]r')

    Which is functionally equivalent to::

        >>> qs = Device.objects.set_query('role=br +role=dr')
    """

    def set_query(self, query, site_id=None, unique=False):
        """
        Filter objects by set theory attribute-value ``query`` patterns.
        """
        objects = self
        if site_id is not None:
            objects = objects.filter(site=site_id)

        try:
            attributes = util.parse_set_query(query)
        except (ValueError, TypeError) as err:
            raise exc.ValidationError({"query": str(err)})

        resource_name = self.model.__name__

        # If there aren't any parsed attributes, don't return anything.
        if not attributes:
            if unique:
                raise exc.ValidationError(
                    {
                        "query": "Query empty, unable to provide %s"
                        % resource_name
                    }
                )
            return objects.none()

        # Iterate a/v pairs and combine query results using MySQL-compatible
        # set operations w/ the ORM
        log.debug("QUERY [start]: objects = %r", objects)
        for action, name, value in attributes:
            # Is this a regex pattern?
            regex_query = False
            if name.endswith("_regex"):
                name = name.replace("_regex", "")  # Keep attribute name
                regex_query = True
                log.debug("Regex enabled for %r" % name)

            # Attribute lookup params
            params = dict(name=name, resource_name=resource_name)
            # Only include site_id if it's set
            if site_id is not None:
                params["site_id"] = site_id

            # If an Attribute doesn't exist, the set query is invalid. Return
            # an empty queryset. (fix #99)
            try:
                attr = Attribute.objects.get(**params)
            except Attribute.DoesNotExist as err:
                raise exc.ValidationError(
                    {"query": "%s: %r" % (str(err).rstrip("."), name)}
                )

            # Set lookup params
            next_set_params = {
                "name": attr.name,
                "value": value,
                "resource_name": resource_name,
            }

            # If it's a regex query, swap ``value`` with ``value__regex``.
            if regex_query:
                next_set_params["value__regex"] = next_set_params.pop("value")

            next_set = Q(
                id__in=Value.objects.filter(**next_set_params).values_list(
                    "resource_id", flat=True
                )
            )

            # This is the MySQL-compatible manual implementation of set theory,
            # baby!
            if action == "union":
                log.debug("SQL UNION")
                objects = objects | self.filter(next_set)
            elif action == "difference":
                log.debug("SQL DIFFERENCE")
                objects = objects.exclude(next_set)
            elif action == "intersection":
                log.debug("SQL INTERSECTION")
                objects = objects.filter(next_set)
            else:
                raise exc.BadRequest("BAD SET QUERY: %r" % (action,))
            log.debug("QUERY [iter]: objects = %r", objects)

        count = objects.count()
        if unique and count != 1:
            # There can be only one
            msg = "Query returned %r results, but exactly 1 expected" % count
            raise exc.ValidationError({"query": msg})
        # Gotta call .distinct() or we might get dupes.
        return objects.distinct()

    def by_attribute(self, name, value, site_id=None):
        """
        Lookup objects by Attribute ``name`` and ``value``.
        """
        resource_name = self.model._meta.model_name.title()
        query = self.filter(
            id__in=Value.objects.filter(
                name=name, value=value, resource_name=resource_name
            ).values_list("resource_id", flat=True)
        )

        if site_id is not None:
            query = query.filter(site=site_id)

        return query


class ResourceManager(models.Manager):
    """
    Manager for Resource objects that adds a special resource methods:

    + ``.set_query()`` - For performing set theory lookups by attribute-value
      string patterns
    + ``.by_attribute()`` - For looking up objects by attribute name/value.

    """

    queryset_class = ResourceSetTheoryQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db)

    def set_query(self, query, site_id=None, unique=False):
        """
        Filter objects by set theory attribute-value string patterns.

        For example::

            >>> Network.objects.set_query('owner=jathan +cluster=sjc'}
            [<Device: foo-bar1>, <Device: foo-bar3>, <Device: foo-bar4>]

            >>> Network.objects.set_query('owner=gary -cluster=sjc'}
            [<Device: foo-bar2>]

            >>> Network.objects.set_query('owner=jathan foo=baz', unique=True}
            [<Device: foo-bar3>]

        :param query:
            Set theory query pattern

        :param site_id:
            ID of Site to filter results

        :param unique:
            Find exactly one match, error otherwise
        """
        return self.get_queryset().set_query(query, site_id, unique)

    def by_attribute(self, name, value, site_id=None):
        """
        Filter objects by Attribute ``name`` and ``value``.

        For example::

            >>> Interface.objects.by_attribute(name='vlan', value=300)
            [<Interface: device=1, name=eth0>]

        :param name:
            Attribute name

        :param value:
            Attribute value

        :param site_id:
            ID of Site to filter results
        """
        return self.get_queryset().by_attribute(name, value, site_id)


class Resource(models.Model):
    """Base for heirarchial Resource objects that may have attributes."""

    _attributes_cache = fields.JSONField(
        null=False,
        blank=True,
        help_text="Local cache of attributes. (Internal use only)",
    )

    # Subclasses set this to the field name to derive site from (e.g., 'device')
    site_source_field = None

    # If True, clean_site() returns Site object; if False, returns site_id
    site_returns_object = False

    # Whether to validate uniqueness in full_clean() during save()
    _validate_unique_on_save = True

    def __init__(self, *args, **kwargs):
        self._set_attributes = kwargs.pop("attributes", None)
        super().__init__(*args, **kwargs)

    class Meta:
        abstract = True

    # Implement .objects.set_query()
    objects = ResourceManager()

    @property
    def attributes(self):
        return Value.objects.filter(
            resource_name=self._resource_name, resource_id=self.id
        )

    @property
    def _resource_name(self):
        return self.__class__.__name__

    def _purge_attribute_index(self):
        self.attributes.all().delete()

    def get_attributes(self):
        """Return the JSON-encoded attributes as a dict."""
        return self._attributes_cache

    def set_attributes(self, attributes, valid_attributes=None, partial=False):
        """Validate and store the attributes dict as a JSON-encoded string.

        When ``partial=True`` (i.e. PATCH), only the provided attributes are
        merged on top of existing ones. Setting a value to ``None`` (JSON
        ``null``) deletes that attribute. Required-attribute validation runs
        against the final merged result to prevent deletion of required keys.
        """
        log.debug("Resource.set_attributes() attributes = %r", attributes)

        # If no attributes and it's a partial update, NOOP.
        if attributes is None and partial:
            return

        if not isinstance(attributes, dict):
            raise exc.ValidationError(
                {
                    "attributes": f"Expected dictionary but received {type(attributes)}"
                }
            )

        # A dict of valid Attribute objects for this resource, keyed by
        # attribute name. If not provided, defaults to all matching
        # resource_name.
        if valid_attributes is None:
            valid_attributes = Attribute.all_by_name(
                self._resource_name, self.site
            )
        log.debug(
            "Resource.set_attributes() valid_attributes = %r", valid_attributes
        )

        # For partial updates, merge incoming attributes with existing ones.
        # Note: concurrent PATCHes on the same resource could race (read-
        # merge-write). This is acceptable for SQLite (serialized writes)
        # and typical single-user IPAM workloads. For high-concurrency
        # deployments, callers should wrap in select_for_update().
        if partial:
            existing = self.get_attributes() or {}

            # Separate deletions (value is None) from updates.
            deletions = {k for k, v in attributes.items() if v is None}
            updates = {k: v for k, v in attributes.items() if v is not None}

            # Validate that all referenced attribute names exist.
            for name in list(deletions) + list(updates.keys()):
                if name not in valid_attributes:
                    msg = f"Attribute name ({name}) does not exist."
                    raise exc.ValidationError({"attributes": msg})

            # Build merged attribute dict: start with existing, apply updates,
            # remove deletions.
            merged = dict(existing)
            merged.update(updates)
            for key in deletions:
                merged.pop(key, None)

            # Use merged as the canonical attributes for the rest of the flow.
            attributes = merged

        # Attributes that are required according to ``valid_attributes``, but
        # are not found in ``attributes``. For partial updates, this validates
        # the final merged result still has all required attributes (preventing
        # deletion of required attributes via null).
        missing_attributes = {
            attribute.name
            for attribute in valid_attributes.values()
            if attribute.required and attribute.name not in attributes
        }
        log.debug(
            "Resource.set_attributes() missing_attributes = %r",
            missing_attributes,
        )

        # It's an error to have any missing attributes
        if missing_attributes:
            names = ", ".join(missing_attributes)
            raise exc.ValidationError(
                {"attributes": f"Missing required attributes: {names}"}
            )

        # Run validation each attribute value and prepare them for DB
        # insertion, raising any validation errors immediately.
        inserts = []
        for name, value in attributes.items():
            if name not in valid_attributes:
                msg = f"Attribute name ({name}) does not exist."
                raise exc.ValidationError({"attributes": msg})

            if not isinstance(name, str):
                raise exc.ValidationError(
                    {"attributes": "Attribute names must be a string type."}
                )

            attribute = valid_attributes[name]
            inserts.extend(attribute.validate_value(value))

        # Purge all of our previously existing attribute values and recreate
        # them anew.
        # FIXME(jathan): This isn't exactly efficient. How can make gud?
        self._purge_attribute_index()
        for insert in inserts:
            Value.objects.create(
                obj=self,
                attribute_id=insert["attribute_id"],
                value=insert["value"],
            )

        self.clean_attributes()

    def clean_attributes(self):
        """Make sure that attributes are saved as JSON."""
        attrs = {}

        # Only fetch the fields we need.
        for a in self.attributes.only("name", "value", "attribute").iterator():
            if a.attribute.multi:
                if a.name not in attrs:
                    attrs[a.name] = []
                attrs[a.name].append(a.value)
            else:
                attrs[a.name] = a.value
        self._attributes_cache = attrs  # Cache the attributes

        return attrs

    def clean_site(self, value):
        """
        Ensure site is set. If not provided, derive from site_source_field.

        Subclasses set site_source_field to the name of the relation field
        to derive site from (e.g., 'device', 'endpoint_a'). Set
        site_returns_object=True to return the Site object instead of site_id.
        """
        # If value is provided and truthy, return as-is
        if value:
            return value

        # If no source field configured, return value as-is
        if self.site_source_field is None:
            return value

        # Try to get the source object
        source = None
        try:
            source = getattr(self, self.site_source_field)
        except self._meta.get_field(
            self.site_source_field
        ).related_model.DoesNotExist:
            # Source relation not loaded; try via FK id
            fk_id = getattr(self, f"{self.site_source_field}_id", None)
            if fk_id is not None:
                field = self._meta.get_field(self.site_source_field)
                source = field.related_model.objects.get(id=fk_id)

        if source is None:
            return value

        # Return either site object or site_id based on class configuration
        if self.site_returns_object:
            site_value = source.site
            if not site_value:
                msg = (
                    "No site was provided and the provided Device does not "
                    "have a site defined"
                )
                raise exc.ValidationError({"site": msg})
            return site_value
        return source.site_id

    def save(self, *args, **kwargs):
        self._is_new = self.id is None  # Check if this is a new object.

        # Use incoming valid_attributes if they are provided.
        valid_attributes = kwargs.pop("valid_attributes", None)

        # Allow subclasses to skip full_clean (e.g., Network does its own)
        skip_full_clean = kwargs.pop("_skip_full_clean", False)
        if not skip_full_clean:
            self.full_clean(validate_unique=self._validate_unique_on_save)

        super().save(*args, **kwargs)

        # This is so that we can set the attributes on create/update, but if
        # the object is new, make sure that it doesn't persist if attributes
        # fail.
        if self._set_attributes is not None:
            try:
                # And set the attributes (if any)
                self.set_attributes(
                    self._set_attributes, valid_attributes=valid_attributes
                )
            except exc.ValidationError:
                # If attributes fail validation, and I'm a new object, delete
                # myself and re-raise the error.
                if self._is_new:
                    self.delete()
                raise
