from email.message import EmailMessage
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, OuterRef
from django.utils import timezone

from registrations.actions.emails import envoyer_email
from registrations.models import TicketEvent, ScannerAction


TEMPLATE = """
Bonjour !

A {heure}, il y avait {billets} émis, et {entrees} entrées pour l'événement « {nom}_».

Cordialement,
Le scanner
""".strip()


class Command(BaseCommand):
    help = "Indique le nombre de billets et d'entrées à un événement"

    def add_arguments(self, parser):
        parser.add_argument("event_id", type=int)
        parser.add_argument("-q", "--quiet", action="store_true")
        parser.add_argument(
            "-s", "--send-to", action="append", dest="recipients", default=[]
        )

    def handle(self, event_id, quiet, recipients, **kwargs):
        try:
            event = TicketEvent.objects.get(id=event_id)
        except TicketEvent.DoesNotExist:
            raise CommandError("Event does not exist")

        billets = event.registration_set.count()
        entrees = (
            event.registration_set.annotate(
                avec_entree=Exists(
                    ScannerAction.objects.filter(
                        registration_id=OuterRef("id"), type=ScannerAction.TYPE_ENTRANCE
                    )
                )
            )
            .filter(avec_entree=True)
            .count()
        )
        heure = (
            timezone.now().astimezone(timezone.get_default_timezone()).strftime("%H:%M")
        )

        stats = TEMPLATE.format(
            heure=heure, billets=billets, entrees=entrees, nom=event.name
        )

        if not quiet:
            self.stdout.write(f"{stats}\n")

        for recipient in recipients:
            envoyer_email(
                recipient=recipient,
                subject=f"Statistiques {event.name} à {heure}",
                body=stats,
            )
