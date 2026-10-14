from django.conf import settings
from django.db import models


class Policy(models.Model):
    name = models.CharField(max_length=200)
    locations = models.JSONField(default=list)  # like owner_ids: the scope
    is_enabled = models.BooleanField(default=True)
    min_approvals = models.PositiveIntegerField(default=1)
    approvers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="policies")


class Condition(models.Model):
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="conditions")
    subject = models.CharField(max_length=50)
    operator = models.CharField(max_length=20)
    value = models.TextField(blank=True)


class Invoice(models.Model):
    vendor = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="draft")  # draft|pending|approved


class Approval(models.Model):
    """TODO Level 1 - design this model. See BRIEF.md for what it must record.

    The given engine code relies on these names:
      invoice      FK to Invoice, reverse accessor `invoice.approvals`
      policy       FK to Policy
      approver     FK to django.contrib.auth User
      state        "waiting" | "active" | "approved" | "inactive"
      approved_at  when it was approved (empty until then)
    Everything else - constraints, on_delete, choices - is your call.
    """
