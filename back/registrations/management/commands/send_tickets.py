from django.core.management.base import BaseCommand, CommandError
import re
import argparse
from functools import reduce
from operator import or_
import tqdm
from smtplib import SMTPServerDisconnected, SMTPRecipientsRefused

from django.db.models import Q
from django.core.mail import get_connection
from django.utils import timezone

from registrations.models import Registration, TicketEvent
from registrations.actions.emails import send_email


class Command(BaseCommand):
    help = "Send tickets to people"

    def add_arguments(self, parser):
        parser.add_argument("event_id", type=int)
        parser.add_argument("registrations_range_start", type=str)
        parser.add_argument("registrations_range_end", nargs="?", type=str)
        parser.add_argument(
            "-i", "--ignore-sent-status", action="store_false", dest="check_sent_status"
        )

    def handle(
        self,
        *args,
        event_id,
        registrations_range_start,
        registrations_range_end=None,
        check_sent_status,
        **options
    ):
        try:
            ticket_event = TicketEvent.objects.get(id=event_id)
        except TicketEvent.DoesNotExist:
            raise CommandError("Event does not exist")

        if ticket_event.send_tickets_until > timezone.now():
            raise CommandError("Date for ticket sending is past")

        if registrations_range_end is not None:
            query = Q(numero__gte=registrations_range_start) & Q(
                numero__lte=registrations_range_end
            )
        else:
            query = Q(numero=registrations_range_start)

        query = query & Q(event=ticket_event)

        if check_sent_status:
            query = query & ~Q(ticket_status=Registration.TICKET_SENT)

        connection = get_connection()

        refused = []

        for elem in tqdm.tqdm(
            Registration.objects.filter(query), desc="Sending tickets"
        ):
            while True:
                try:
                    send_email(elem, connection=connection)
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
