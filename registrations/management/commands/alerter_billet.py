from collections import Counter
from email.message import EmailMessage
import time
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, OuterRef
from django.utils import timezone

from registrations.models import Registration, ScannerAction
from registrations.actions.emails import envoyer_email


DEFAULT_POLLING_TIME = 5


class Command(BaseCommand):
    help = "Signale (via du texte ou un email) quand un billet spécifique a été vu."

    def add_arguments(self, parser):
        parser.add_argument("ticket_id", type=int)
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Ne pas écrire l'alerte sur la sortie erreur standard.",
        )
        parser.add_argument(
            "-s", "--send-to", action="append", dest="recipients", default=[]
        )
        parser.add_argument(
            "-p", "--polling-time", type=int, default=DEFAULT_POLLING_TIME
        )

    def handle(self, ticket_id, quiet, recipients, polling_time, **kwargs):
        try:
            ticket = Registration.objects.get(id=ticket_id)
        except Registration.DoesNotExist:
            raise CommandError("Billet introuvable.")
        nom = f"{ticket.full_name} ({ticket.event.name})"

        events = ticket.events.all()
        seen = {e.id for e in events}
        c = Counter(e.get_type_display() for e in events)
        decomptes = " / ".join(f"{k}={v}" for k, v in c.items())

        if not quiet:
            self.stdout.write(f"Alertes pour {nom}")
            self.stdout.write(f"Événements initiaux : {decomptes}\n")

        while True:
            time.sleep(polling_time)
            actions = ticket.events.exclude(id__in=seen).order_by("time")
            if actions:
                description = "\n".join(
                    f"[{a.time.strftime('%H:%M')}] Action {a.get_type_display()}"
                    for a in actions
                )

                if len(actions) > 1:
                    intro = f"Les actions suivantes ont été effectées"
                else:
                    intro = f"L'action suivante a été effectué"

                body = f"{intro}\n{description}"

                if not quiet:
                    self.stdout.write(f"{description}\n")

                for r in recipients:
                    envoyer_email(
                        recipient=r,
                        subject=f"Nouvelles actions pour {nom}",
                        body=body,
                    )
