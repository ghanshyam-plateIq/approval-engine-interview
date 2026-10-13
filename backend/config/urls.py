from django.urls import include, path

urlpatterns = [path("", include("approvals.urls"))]
