from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.views import HealthView

urlpatterns = [path("api/v1/health/", HealthView.as_view(), name="health")]
urlpatterns += [path("api/v1/auth/", include("apps.accounts.urls"))]
urlpatterns += [path("api/v1/", include("apps.events.urls"))]
if settings.DEBUG:
    urlpatterns += [
        path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    ]
