########
REST API
########

NSoT is designed as an API-first application so that all possible actions are
published as API endpoints.

.. _dynamic-field-selection:

Dynamic Field Selection
=======================

All resource endpoints support three query parameters for controlling which
fields appear in the response:

``?fields=field1,field2``
    **Sparse fieldsets** — only return the specified fields.

``?omit=field1,field2``
    **Exclude fields** — return everything except the listed fields.

``?expand=field1,field2``
    **Expand related objects** — replace foreign-key values with the full
    nested object.

These parameters can be combined freely and work on both list and detail
endpoints.

Fields & Omit
-------------

Return only ``id`` and ``hostname`` for devices:

.. code-block:: bash

    $ curl -s "http://localhost:8990/api/sites/1/devices/?fields=id,hostname"

Return devices without the ``attributes`` key:

.. code-block:: bash

    $ curl -s "http://localhost:8990/api/sites/1/devices/?omit=attributes"

Expand
------

By default, related objects are represented as IDs or natural keys. Use
``?expand`` to inline the full object.

Expand the site on a device:

.. code-block:: bash

    $ curl -s "http://localhost:8990/api/sites/1/devices/?expand=site_id"

    [
        {
            "id": 1,
            "hostname": "foo-bar1",
            "site_id": {
                "id": 1,
                "name": "Test Site",
                ...
            },
            "attributes": {}
        }
    ]

Expand the device on an interface:

.. code-block:: bash

    $ curl -s "http://localhost:8990/api/sites/1/interfaces/?expand=device"

Deep (dot-notation) expansion is also supported:

.. code-block:: bash

    $ curl -s "http://localhost:8990/api/sites/1/interfaces/?expand=device.site_id"

Expandable Fields Reference
----------------------------

========== ========================
Resource   Expandable fields
========== ========================
Device     ``site_id``
Network    ``site_id``, ``parent_id``
Interface  ``device``, ``parent_id``
Attribute  ``site_id``
========== ========================

Unknown expand values are silently ignored.

.. _api-ref:

API Reference
=============

Interactive API reference documentation can be found by browsing to ``/docs/``
on a running NSoT server instance.

.. _browsable-api:

Browsable API
=============

Because NSoT is an API-first application, the REST API is central to the
experience. The REST API can support JSON or can also be used directly from
your web browser. This version is called the "browsable API" and while it
doesn't facilitate automation, it can be very useful.

Visit ``/api/`` in your browser on your installed instance. How cool is that?!

.. _api-auth:

Authentication
==============

Two methods of authentication are currently supported.

.. _api-auth_header:

User Authentication Header
--------------------------

This is referred to internally as **auth_header** authentication.

In normal operation NSoT is expected to be run behind an authenticating proxy
that passes back a specific header. By default we expect ``X-NSoT-Email``,
though it is configurable using the ``USER_AUTH_HEADER`` setting.

The value of this header must be the user's ``email`` and is formatted like
so:

.. code-block:: javascript

    X-NSoT-Email: {email}

.. _api-auth_token:

AuthToken
---------

This is referred to internally as **auth_token** authentication.

API authentication requires the ``email`` and ``secret_key``
of a user. When a user is first created, a ``secret_key`` is automatically
generated. The user may obtain their ``secret_key`` from the web interface.

Users make a POST request to ``/api/authenticate/`` to passing ``email`` and
``secret_key`` in ``JSON`` payload. They are returned an ``auth_token`` that can
then be used to make API calls. The ``auth_token`` is short-lived (default is
10 minutes and can be change using the ``AUTH_TOKEN_EXPIRY`` setting). Once the
token expires a new one must be obtained.

The ``auth_token`` must be sent to the API using an ``Authorization`` header
that is formatted like so:

.. code-block:: javascript

    Authorization: AuthToken {email}:{secret_key}

Requests
========

In addition to the authentication header above all ``POST``, ``PUT``, and
``PATCH``, requests will be sent as ``JSON`` rather than form data and should
include the header ``Content-Type: application/json``

``PUT`` requests are of note as they are expected to set the state of all
mutable fields on a resource. This means if you don't specificy all optional
fields may revert to their default values, depending on the object type.

``PATCH`` allows for partial update of objects for most fields, depending on
the object type.

.. _partial-attribute-update:

Partial Attribute Updates (PATCH)
---------------------------------

When using ``PATCH`` to update a resource, attributes are merged with the
existing attributes rather than replacing them entirely. This allows you to
update individual attributes without needing to send the complete attribute
dictionary.

* Providing ``{"attributes": {"key": "value"}}`` will add or update that
  attribute while leaving all other existing attributes unchanged.
* Setting an attribute to ``null`` will delete it:
  ``{"attributes": {"key": null}}``.
* Required attributes cannot be deleted; attempting to do so will return a
  validation error.

For example, if a device has ``{"owner": "jathan", "vendor": "juniper"}`` and
you PATCH with ``{"attributes": {"vendor": "arista"}}``, the result will be
``{"owner": "jathan", "vendor": "arista"}``.

.. _bulk-delete:

Bulk Delete
-----------

Multiple resources can be deleted in a single request by sending a ``DELETE``
request to the resource list endpoint with a JSON body containing a list of
integer IDs.

**Request**:

.. code-block:: http

    DELETE /api/sites/1/devices/
    Content-Type: application/json

    [1, 2, 3]

**Response**:

.. code-block:: javascript

    HTTP 204 No Content

Each object's permissions are validated before deletion. All IDs must be
integers. If any ID is invalid or not found, the request will return an error.
Duplicate IDs are automatically deduplicated.

``OPTIONS`` will provide the schema for any endpoint.

Responses
=========

All responses will be in format along with the header ``Content-Type:
application/json`` set.

The ``JSON`` payload will be in one of two potential structures and will always
contain a ``status`` field to distinguish between them. If the ``status`` field
has a value of ``"ok"``, then the request was successful and the response will
be available in the ``data`` field.

.. code-block:: javascript

    {
        ...
    }

If the ``status`` field has a value of ``"error"`` then the response failed
in some way. You will have access to the error from the ``error`` field which
will contain an error ``code`` and ``message``.

.. code-block:: javascript

    {
        "error": {
            "code": 404,
            "message": "Resource not found."
        }
    }

Pagination
==========

All responses that return a list of resources will support pagination. If the
``results`` object on the response has a ``count`` attribute then the endpoint
supports pagination. When making a request against this endpoint ``limit`` and
``offset`` query parameters are supported.

The response will also include ``next`` and ``previous`` URLs that can be used
to retrieve the next set of results. If there are not any more results
available, their value will be ``null``.

An example response for querying the ``sites`` endpoint might look like:

**Request**:

.. code-block:: http

    GET http://localhost:8990/api/sites/?limit=1&offset=0

**Response**:

.. code-block:: javascript

    {
        "count": 1,
        "next": "http://localhost:8990/api/sites/?limit=1&offset=1",
        "previous": null,
        "results": [
            {
                "id": 1
                "name": "Site 1",
                "description": ""
            }
        ]
    }

Schemas
=======

By performing an ``OPTIONS`` query on any endpoint, you can obtain the schema
of the resource for that endpoint. This includes supported content-types, HTTP
actions, the fields allowed for each action, and their attributes.

An example response for the schema for the ``devices`` endpoint might look like:

**Request**:

.. code-block:: http

    OPTIONS http://localhost:8990/api/devices/

**Response**:

.. code-block:: javascript

    HTTP 200 OK
    Allow: GET, POST, PUT, PATCH, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    {
        "name": "Device List",
        "description": "API endpoint that allows Devices to be viewed or edited.",
        "renders": [
            "application/json",
            "text/html"
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ],
        "actions": {
            "PUT": {
                "id": {
                    "type": "integer",
                    "required": false,
                    "read_only": true,
                    "label": "ID"
                },
                "hostname": {
                    "type": "string",
                    "required": true,
                    "read_only": false,
                    "label": "Hostname",
                    "max_length": 255
                },
                "attributes": {
                    "type": "field",
                    "required": true,
                    "read_only": false,
                    "label": "Attributes",
                    "help_text": "Dictionary of attributes to set."
                }
            },
            "POST": {
                "hostname": {
                    "type": "string",
                    "required": true,
                    "read_only": false,
                    "label": "Hostname",
                    "max_length": 255
                },
                "attributes": {
                    "type": "field",
                    "required": false,
                    "read_only": false,
                    "label": "Attributes",
                    "help_text": "Dictionary of attributes to set."
                },
                "site_id": {
                    "type": "integer",
                    "required": true,
                    "read_only": false,
                    "label": "Site id"
                }
            }
        }
    }

.. _api-set-queries:

Performing Set Queries
======================

:ref:`set-queries` allow you to perform complex lookups of objects by
attribute/value pairs and are available on all :ref:`resources` at the
``/api/:resource/query/`` list endpoint for a given resource type.

To perform a set query you must perform a ``GET`` request to the query endpoint
providing the set query string as a value to the ``query`` argument.

For example:

**Request**:

.. code-block:: http

   GET /api/devices/query/?query=vendor=juniper

**Response**:

.. code-block:: javascript

    HTTP 200 OK
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    [
        {
            "attributes": {
                "owner": "jathan",
                "vendor": "juniper",
                "hw_type": "router",
                "metro": "lax"
            },
            "hostname": "lax-r2",
            "site_id": 1,
            "id": 2
        },
        {
            "attributes": {
                "owner": "jathan",
                "vendor": "juniper",
                "hw_type": "router",
                "metro": "iad"
            },
            "hostname": "iad-r1",
            "site_id": 1,
            "id": 5
        }
    ]

The optional ``unique`` argument can also be provided in order to ensure only
a single object is returned, otherwise an error is returned.

**Request**:

.. code-block:: http

   GET /api/devices/query/?query=metro=iad&unique=true

**Response**:

.. code-block:: javascript

    HTTP 200 OK
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    [
        {
            "attributes": {
                "owner": "jathan",
                "vendor": "juniper",
                "hw_type": "router",
                "metro": "iad"
            },
            "hostname": "iad-r1",
            "site_id": 1,
            "id": 5
        }
    ]

If multiple results match the query, when ``unique`` has been specified,
an error will be returned.

**Request**:

.. code-block:: http

   GET /api/devices/query/?query=vendor=juniper

**Response**:

.. code-block:: javascript

    HTTP 400 Bad Request
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    {
        "error": {
            "message": {
                "query": "Query returned 2 results, but exactly 1 expected"
            },
            "code": 400
        }
    }
