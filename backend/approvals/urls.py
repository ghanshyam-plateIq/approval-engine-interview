from django.urls import path

from . import views

urlpatterns = [
    path("api/invoices/<int:invoice_id>/", views.invoice_detail),
    path("api/invoices/<int:invoice_id>/policies/", views.invoice_policies),
    path("api/invoices/<int:invoice_id>/submit/", views.submit),
    path("api/invoices/<int:invoice_id>/approve/", views.approve),
    path("api/users/", views.users),
    path("api/users/<str:username>/queue/", views.queue),
    path("api/reports/approver-load/", views.approver_load),
    path("inbox/", views.inbox),
]
