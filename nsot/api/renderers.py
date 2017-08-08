from __future__ import unicode_literals

from rest_framework.renderers import BrowsableAPIRenderer


class FilterlessBrowsableAPIRenderer(BrowsableAPIRenderer):
    """Custom browsable API renderer that doesn't show filter forms."""
    def get_filter_form(self, data, view, request):
        """
        Disable filter form display.

        This is because of major performance problems with large installations,
        especially with large sets of related objects.

        FIXME(jathan): Revisit this after browsable API rendering has improved
        in future versions of DRF.
        """
        return


# TODO(jathan): Clean this up before final release.
import coreapi
from coreapi.compat import force_bytes
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework import status
from rest_framework_swagger import renderers as swagger_renderers
from rest_framework_swagger.settings import swagger_settings
import simplejson as json


class OpenAPICodec(swagger_renderers.OpenAPICodec):
    def encode(self, document, extra=None, **options):
        # import ipdb; ipdb.set_trace()
        return super(OpenAPICodec, self).encode(document, extra=extra,
                                                **options)

    def decode(self, bytes, **options):
        return super(OpenAPICodec, self).decode(bytes, **options)


class OpenAPIRenderer(swagger_renderers.OpenAPIRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context['response'].status_code != status.HTTP_200_OK:
            return JSONRenderer().render(data)
        extra = self.get_customizations(data)
        # import ipdb; ipdb.set_trace()

        return OpenAPICodec().encode(data, extra=extra)

    def get_customizations(self, data):
        """
        Adds settings, overrides, etc. to the specification.
        """
        extra = {}
        if swagger_settings.SECURITY_DEFINITIONS:
            extra['securityDefinitions'] = swagger_settings.SECURITY_DEFINITIONS

        return extra
