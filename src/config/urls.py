from django.urls import include, path, re_path
from django.views.generic import TemplateView


urlpatterns = [
    path("api/", include("src.api.urls")),
    re_path(r"^(?!api/).*", TemplateView.as_view(template_name="index.html"), name="spa-entry"),
]
