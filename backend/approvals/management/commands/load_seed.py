import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from approvals.models import Condition, Invoice, Policy

SEED = Path(__file__).resolve().parents[3] / "seed.json"


class Command(BaseCommand):
    help = "Wipe approval data and load seed.json (safe to run repeatedly)."

    @transaction.atomic
    def handle(self, *args, **options):
        data = json.loads(SEED.read_text())
        Invoice.objects.all().delete()
        Policy.objects.all().delete()
        User.objects.all().delete()
        users = {name: User.objects.create(username=name) for name in data["users"]}
        for p in data["policies"]:
            approvers, conditions = p.pop("approvers"), p.pop("conditions")
            policy = Policy.objects.create(**p)
            policy.approvers.set(users[u] for u in approvers)
            Condition.objects.bulk_create(Condition(policy=policy, **c) for c in conditions)
        Invoice.objects.bulk_create(Invoice(**i) for i in data["invoices"])
