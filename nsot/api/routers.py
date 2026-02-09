from rest_framework_nested.routers import NestedSimpleRouter

from nsot.vendor.rest_framework_bulk.routes import BulkRouter

__all__ = ("BulkNestedRouter", "BulkRouter")

# Map of HTTP verbs to rest_framework_bulk operations.
BULK_OPERATIONS_MAP = {
    "put": "bulk_update",
    "patch": "partial_bulk_update",
    "delete": "bulk_destroy",
}


class BulkNestedRouter(NestedSimpleRouter):
    """
    Bulk-enabled nested router.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.routes[0].mapping.update(BULK_OPERATIONS_MAP)
