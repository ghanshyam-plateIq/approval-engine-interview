import json
from pathlib import Path

from django.core.management.base import BaseCommand

SEED = Path(__file__).resolve().parents[3] / "seed.json"


class Command(BaseCommand):
    help = "Wipe approval data and load seed.json (safe to run repeatedly)."

    def handle(self, *args, **options):
        data = json.loads(SEED.read_text())
        # TODO: wipe existing rows, then create users, policies (with approvers + conditions) and invoices.
        # Keep the ids from seed.json - the API is addressed by them.
        raise NotImplementedError
