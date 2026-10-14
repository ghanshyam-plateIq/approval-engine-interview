"""The approval engine.

GIVEN - policy matching: which policies apply to an invoice.
GIVEN (slow) - the approval lifecycle: apply_policies, recompute, approve. Level 1: make it fast.
YOUR JOB - unapprove (Level 3).
"""

from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Approval, Invoice, Policy  # noqa: F401

# ============================================================== GIVEN: policy matching

AND_SUBJECTS = {"vendor_is_not"}


def condition_passes(invoice, c):
    if c.subject == "total_amount":
        value = Decimal(c.value)
        return invoice.total >= value if c.operator == "gte" else invoice.total <= value
    if c.subject == "vendor":
        return invoice.vendor == c.value
    if c.subject == "vendor_is_not":
        return invoice.vendor != c.value
    if c.subject == "catch_all":
        return True
    raise ValueError(f"unknown subject {c.subject}")


def conditions_match(invoice, conditions):
    groups = defaultdict(list)
    for c in conditions:
        groups[(c.subject, c.operator)].append(c)
    return all(
        (all if subject in AND_SUBJECTS else any)(condition_passes(invoice, c) for c in group)
        for (subject, _), group in groups.items()
    )


def parent_ids(policy):
    return {int(c.value) for c in policy.conditions.all() if c.subject == "has_policy"}


def applicable_policies(invoice, include_dependents=True):
    """Every policy that applies: direct matches, catch-all fallback, then has_policy dependents."""
    in_scope = [
        p for p in Policy.objects.filter(is_enabled=True).prefetch_related("conditions")
        if invoice.location in p.locations
    ]
    direct, fallback, dependents = [], [], []
    for p in in_scope:
        conds = list(p.conditions.all())
        if parent_ids(p):
            dependents.append(p)
        elif conditions_match(invoice, conds):
            (fallback if any(c.subject == "catch_all" for c in conds) else direct).append(p)
    applied = direct or fallback
    if include_dependents:
        changed = True
        while changed:  # dependents of dependents
            changed = False
            ids = {p.id for p in applied}
            for p in dependents:
                rest = [c for c in p.conditions.all() if c.subject != "has_policy"]
                if p.id not in ids and parent_ids(p) <= ids and conditions_match(invoice, rest):
                    applied.append(p)
                    changed = True
    return sorted(applied, key=lambda p: p.id)


# ============================================================== GIVEN (works, but slow): lifecycle
#
# Approval.state is one of:
#   waiting  - disabled: its policy depends on a parent policy that isn't satisfied yet
#   active   - in the approver's queue, can be approved
#   approved - approved by that user
#   inactive - its policy is already satisfied by other approvers
#
# Everything below is CORRECT - the hidden checks for behaviour already pass.
# It is also SLOW: Level 1 asks you to make it fast without changing what it does.


@transaction.atomic
def apply_policies(invoice: Invoice) -> None:
    """Sync approval rows to the policies that apply now (keep / add / drop), then recompute."""
    policies = applicable_policies(invoice)
    policy_ids = [p.id for p in policies]

    for approval in invoice.approvals.all():
        if approval.policy_id not in policy_ids:
            approval.delete()

    for policy in policies:
        for approver in policy.approvers.all():
            if not Approval.objects.filter(invoice=invoice, policy=policy, approver=approver).exists():
                Approval.objects.create(invoice=invoice, policy=policy, approver=approver, state="waiting")

    recompute(invoice)


def recompute(invoice: Invoice) -> None:
    """Derive every non-approved row's state, and the invoice status, from what's been approved."""
    satisfied = set()
    policy_ids = set(invoice.approvals.values_list("policy_id", flat=True))
    for policy in Policy.objects.filter(id__in=policy_ids):
        approved = Approval.objects.filter(invoice=invoice, policy=policy, state="approved").count()
        if approved >= policy.min_approvals:
            satisfied.add(policy.id)

    for approval in invoice.approvals.all():
        if approval.state == "approved":
            continue
        if approval.policy_id in satisfied:
            approval.state = "inactive"
        elif parent_ids(approval.policy) <= satisfied:
            approval.state = "active"
        else:
            approval.state = "waiting"
        approval.save()

    invoice.status = "approved" if satisfied == policy_ids else "pending"
    invoice.save()


@transaction.atomic
def approve(invoice: Invoice, user) -> bool:
    """Approve every active approval this user holds on the invoice. False if they had none."""
    approved_any = False
    for approval in Approval.objects.filter(invoice=invoice):
        if approval.approver.username == user.username and approval.state == "active":
            approval.state = "approved"
            approval.approved_at = timezone.now()
            approval.save()
            approved_any = True
    if approved_any:
        recompute(invoice)
    return approved_any


# ============================================================== YOUR JOB (Level 3)


@transaction.atomic
def unapprove(invoice: Invoice, user) -> bool:
    """Withdraw every approval this user gave on the invoice, then re-derive states.
    False if they had no approved rows. (Level 3)"""
    # TODO Level 3
    raise NotImplementedError
