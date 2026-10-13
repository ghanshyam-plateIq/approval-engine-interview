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
    """One row per (invoice, policy, approver) - the ObjectApproval equivalent."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="approvals")
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals")
    state = models.CharField(max_length=20)  # waiting|active|approved|inactive
    approved_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["invoice", "policy", "approver"], name="uniq_approval")]
        indexes = [models.Index(fields=["approver", "state"])]
