import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import engine
from .models import Invoice


def body(request) -> dict:
    return json.loads(request.body or "{}")


def money(value) -> str:
    return f"{value:.2f}"


def serialize(invoice: Invoice) -> dict:
    return {
        "id": invoice.id,
        "vendor": invoice.vendor,
        "location": invoice.location,
        "total": money(invoice.total),
        "status": invoice.status,
        "approvals": [
            {"policy_id": a.policy_id, "approver": a.approver.username, "state": a.state}
            for a in invoice.approvals.select_related("approver").order_by("policy_id", "approver__username")
        ],
    }


def invoice_row(invoice: Invoice) -> dict:
    return {"id": invoice.id, "vendor": invoice.vendor, "location": invoice.location, "total": money(invoice.total)}


# ---------------------------------------------------------------- GIVEN


@require_GET
def invoice_policies(request, invoice_id):
    """Debug helper: the non-dependent policies that match."""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    return JsonResponse({"policy_ids": [p.id for p in engine.applicable_policies(invoice, include_dependents=False)]})


@require_http_methods(["GET", "PATCH"])
@transaction.atomic
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_for_update(), pk=invoice_id)
    if request.method == "PATCH":
        data = body(request)
        for field in ("vendor", "location"):
            if field in data:
                setattr(invoice, field, data[field])
        if "total" in data:
            invoice.total = Decimal(data["total"])
        invoice.save()
        if invoice.status != "draft":
            engine.apply_policies(invoice)
    return JsonResponse(serialize(invoice))


@require_POST
@transaction.atomic
def submit(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_for_update(), pk=invoice_id)
    if invoice.status != "draft":
        return JsonResponse({"error": "not a draft"}, status=409)
    engine.apply_policies(invoice)
    return JsonResponse(serialize(invoice))


@require_POST
@transaction.atomic
def approve(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_for_update(), pk=invoice_id)
    if invoice.status != "pending":
        return JsonResponse({"error": "invoice is not pending"}, status=409)
    user = User.objects.filter(username=body(request).get("user")).first()
    if user is None or not engine.approve(invoice, user):
        return JsonResponse({"error": "nothing for you to approve"}, status=403)
    return JsonResponse(serialize(invoice))


# ---------------------------------------------------------------- Level 4: YOUR JOB

# TODO Level 4: POST /api/invoices/<id>/unapprove/ - write the view here, then add its URL in urls.py.


# ---------------------------------------------------------------- Level 5: GIVEN (slow)


@require_GET
def queue(request, username):
    """Invoices where `username` holds an active approval, each once, total desc then id.

    Level 5: make this one efficient query, and add the index it needs.
    """
    user = get_object_or_404(User, username=username)
    invoices = []
    for invoice in Invoice.objects.all():
        for approval in invoice.approvals.all():
            if approval.approver_id == user.id and approval.state == "active":
                invoices.append(invoice)
                break
    invoices.sort(key=lambda i: (-i.total, i.id))
    return JsonResponse([invoice_row(i) for i in invoices], safe=False)


# ---------------------------------------------------------------- Bonus


@require_GET
def approver_load(request):
    # TODO Bonus: one query, every approver -> {"approver", "pending_invoices", "pending_amount"}
    rows = []
    return JsonResponse(rows, safe=False)
