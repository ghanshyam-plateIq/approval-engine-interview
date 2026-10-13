"""The approval engine.

GIVEN - policy matching: which policies apply to an invoice (read it, you'll be asked about it).
YOUR JOB - the approval lifecycle: apply_policies, recompute, approve, unapprove.
"""

from collections import defaultdict  # noqa: F401
from decimal import Decimal

from django.db import transaction
from django.utils import timezone  # noqa: F401

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


# ============================================================== YOUR JOB: the lifecycle
#
# Approval.state is one of:
#   waiting  - disabled: its policy depends on a parent policy that isn't satisfied yet (Layer 4)
#   active   - in the approver's queue, can be approved
#   approved - approved by that user
#   inactive - its policy is already satisfied by other approvers


@transaction.atomic
def apply_policies(invoice: Invoice) -> None:
    """Create approval rows for every applicable policy, then set states + invoice status.

    Layer 2: one Approval per (policy, approver) for applicable_policies(invoice, include_dependents=False).
    Layer 4: include dependent policies - their rows start disabled (`waiting`).
    Layer 7: keep / add / delete rows so they match the policies that apply *now*.
    """
    # TODO Layer 2
    raise NotImplementedError


def recompute(invoice: Invoice) -> None:
    """Derive every non-approved row's state, and the invoice status, from what's been approved.

    Layer 2: rows `active`; no rows -> invoice approved, otherwise pending.
    Layer 3: satisfied policies' open rows -> `inactive`; all policies satisfied -> invoice approved.
    Layer 4: a dependent's rows stay `waiting` until all its parent policies are satisfied.
    """
    # TODO Layer 2 / 3 / 4
    raise NotImplementedError


@transaction.atomic
def approve(invoice: Invoice, user) -> bool:
    """Approve every active approval this user holds on the invoice. False if none. (Layer 3)"""
    # TODO Layer 3
    raise NotImplementedError


@transaction.atomic
def unapprove(invoice: Invoice, user) -> bool:
    """Withdraw this user's approvals on the invoice. False if they had none. (Layer 5)"""
    # TODO Layer 5
    raise NotImplementedError
