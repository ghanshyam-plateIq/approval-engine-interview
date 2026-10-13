"""The approval engine. Views call into this module - keep the rules here."""

from collections import defaultdict  # noqa: F401
from decimal import Decimal

from django.db import transaction
from django.utils import timezone  # noqa: F401

from .models import Approval, Invoice, Policy  # noqa: F401

AND_SUBJECTS = {"vendor_is_not"}  # groups of these subjects need ALL conditions true


def condition_passes(invoice: Invoice, condition) -> bool:
    """Is a single condition true for this invoice? (see the subjects table in BRIEF.md)"""
    if condition.subject == "total_amount" and condition.operator == "gte":
        return invoice.total >= Decimal(condition.value)
    # TODO Layer 1: total_amount lte, vendor, vendor_is_not, catch_all
    raise NotImplementedError(condition.subject)


def conditions_match(invoice: Invoice, conditions) -> bool:
    """Do these conditions match? Apply the grouping rules from BRIEF.md."""
    # TODO Layer 1
    raise NotImplementedError


def applicable_policies(invoice: Invoice, include_dependents: bool = True) -> list[Policy]:
    """Every policy that applies to the invoice, sorted by id.

    Layer 1: enabled + location scope + conditions + catch-all fallback; skip has_policy policies.
    Layer 3: when include_dependents is True, also add has_policy dependents.
    """
    # TODO Layer 1 (and Layer 3)
    raise NotImplementedError


@transaction.atomic
def apply_policies(invoice: Invoice) -> None:
    """Create the approval rows for the applicable policies and set the invoice status.

    Layer 2: one Approval per (policy, approver).
    Layer 6: keep / add / delete rows so they match the policies that apply now.
    """
    # TODO Layer 2
    raise NotImplementedError


def recompute(invoice: Invoice) -> None:
    """Derive every approval's state and the invoice status from what's been approved. (Layer 3)"""
    # TODO Layer 3
    raise NotImplementedError


@transaction.atomic
def approve(invoice: Invoice, user) -> bool:
    """Approve this user's active approvals on the invoice. False if they had none. (Layer 3)"""
    # TODO Layer 3
    raise NotImplementedError
