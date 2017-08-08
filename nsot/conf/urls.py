from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

from ..api import routers
from ..api.views import NotFoundViewSet
from ..ui.views import FeView


# Custom error-handling views.
handler400 = 'nsot.ui.views.handle400'
handler403 = 'nsot.ui.views.handle403'
handler404 = 'nsot.ui.views.handle404'
handler500 = 'nsot.ui.views.handle500'


# TODO(jathan): Clean me up before final release.
from rest_framework import renderers as rest_renderers
from rest_framework import schemas
from rest_framework_swagger import renderers as swagger_renderers
from ..api import renderers as nsot_renderers

swagger_renderer_classes = [
	rest_renderers.CoreJSONRenderer,
    # swagger_renderers.OpenAPIRenderer,
    nsot_renderers.OpenAPIRenderer,
    swagger_renderers.SwaggerUIRenderer,
]

# These are all the arguments available and their defaults
schema_view = schemas.get_schema_view(
    title='nsot-api',
    # url=None,
    # description=None,
    # urlconf=None,
    # renderer_classes=None,
    renderer_classes=swagger_renderer_classes,
    # public=False,
    # patterns=None,
    # generator_class=schemas.SchemaGenerator,
    generator_class=routers.NsotSchemaGenerator,

)
# The above replaces this:
'''
from rest_framework_swagger.views import get_swagger_view
schema_view = get_swagger_view(title='nsot-api')
'''


from rest_framework.documentation import include_docs_urls

API_TITLE = 'NSOT API TITLE'
API_DESCRIPTION = 'NSOT API DESCRIPTION'

docs_view = include_docs_urls(title=API_TITLE, description=API_DESCRIPTION,
                              generator_class=routers.NsotSchemaGenerator)

urlpatterns = [
    # API
    url(r'^api/', include('nsot.api.urls')),

    # Catchall for missing endpoints
    url(r'^api/.*/$', NotFoundViewSet.as_view({'get': 'list'})),

    # Docs (Swagger)
    # url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^docs/', docs_view),  # Built-in API docs (DRF 3.6)
    url(r'^schema/', schema_view),  # Swagger 2.0 schema)

    # Admin
    url(r'^admin/', include(admin.site.urls)),

    # Favicon redirect for when people insist on fetching it from /favicon.ico
    url(
        r'^favicon\.ico$',
        RedirectView.as_view(
            url='%sbuild/images/favicon/favicon.ico' % settings.STATIC_URL,
            permanent=True
        ),
        name='favicon'
    ),

    # Smart selects chaining
    url(r'^chaining/', include('smart_selects.urls')),

    # FE handlers
    # Catch index
    url(r'^$', FeView.as_view(), name='index'),

    # Catch all for remaining URLs
    url(r'^.*/$', FeView.as_view(), name='index'),
]
