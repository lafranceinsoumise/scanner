from smtplib import SMTPServerDisconnected, SMTPRecipientsRefused

import tqdm
from django.core.mail import get_connection
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from registrations.actions.emails import envoyer_billet
from registrations.models import Registration, TicketEvent


class Command(BaseCommand):
    help = "Send tickets to people"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.dry_run = None

    def add_arguments(self, parser):
        parser.add_argument("event_id", type=int)
        parser.add_argument("registrations_range_start", nargs="?", type=str)
        parser.add_argument("registrations_range_end", nargs="?", type=str)
        parser.add_argument("-c", "--category_id", nargs="?", type=int)
        parser.add_argument(
            "-i", "--ignore-sent-status", action="store_false", dest="check_sent_status"
        )
        parser.add_argument(
            "-d", "--dry-run", action="store_false", dest="dry_run"
        )

    def handle(
        self,
        *args,
        event_id,
        registrations_range_start=None,
        registrations_range_end=None,
        check_sent_status,
        category_id=None,
        dry_run,
        **options
    ):
        try:
            ticket_event = TicketEvent.objects.get(id=event_id)
        except TicketEvent.DoesNotExist:
            raise CommandError("Event does not exist")

        if timezone.now() > ticket_event.send_tickets_until:
            raise CommandError("Date for ticket sending is past")

        query = Q()
        if registrations_range_end is not None:
            query = Q(numero__gte=registrations_range_start) & Q(
                numero__lte=registrations_range_end
            )
        elif registrations_range_start is not None:
            query = Q(numero=registrations_range_start)

        if category_id is not None:
            query = query & Q(category=category_id)

        query = query & Q(event=ticket_event) & Q(canceled=False)

        if check_sent_status:
            query = query & ~Q(ticket_status=Registration.TICKET_SENT)

        self.dry_run = dry_run

        connection = get_connection()

        refused = []

        if dry_run:
            self.stdout.write(
                "Sending {} tickets".format(Registration.objects.filter(query).count())
            )
            return

        for elem in tqdm.tqdm(
            Registration.objects.filter(query), desc="Sending tickets"
        ):
            while True:
                try:
                    envoyer_billet(elem, connection=connection)
                except SMTPServerDisconnected:
                    connection = get_connection()
                    continue
                except SMTPRecipientsRefused:
                    refused.append(elem)
                    break
                break

        connection.close()

        for elem in refused:
            self.stdout.write(
                "Could not send to {} ({})".format(elem.contact_email, elem.numero)
            )
