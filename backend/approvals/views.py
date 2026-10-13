import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
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


# ---------------------------------------------------------------- Layer 1


@require_GET
def invoice_policies(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    # TODO Layer 1: {"policy_ids": [...]} using engine.applicable_policies(invoice, include_dependents=False)
    return JsonResponse({"error": "not implemented"}, status=501)


# ---------------------------------------------------------------- Layer 2


@require_POST
@transaction.atomic
def submit(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_for_update(), pk=invoice_id)
    # TODO Layer 2: 409 unless draft, then engine.apply_policies(invoice)
    return JsonResponse(serialize(invoice))


@require_GET
def queue(request, username):
    user = get_object_or_404(User, username=username)
    # TODO Layer 2: invoices where `user` has an active approval, each once, total desc then id
    invoices = Invoice.objects.none()
    return JsonResponse([invoice_row(i) for i in invoices], safe=False)


# ---------------------------------------------------------------- Layer 3


@require_POST
@transaction.atomic
def approve(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_for_update(), pk=invoice_id)
    user = User.objects.filter(username=body(request).get("user")).first()
    # TODO Layer 3: 409 / 403 rules, then engine.approve(invoice, user)
    return JsonResponse(serialize(invoice))


# ---------------------------------------------------------------- Layer 4


@require_GET
def approver_load(request):
    # TODO Layer 4: one query, every approver -> {"approver", "pending_invoices", "pending_amount"}
    rows = []
    return JsonResponse(rows, safe=False)


# ---------------------------------------------------------------- Layer 5


@require_GET
def users(request):
    return JsonResponse(list(User.objects.order_by("username").values_list("username", flat=True)), safe=False)


def inbox(request):
    return render(request, "inbox.html")


# ---------------------------------------------------------------- Detail (+ Layer 6)


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
        # TODO Layer 6: re-evaluate approvals when the invoice isn't a draft
    return JsonResponse(serialize(invoice))
