from django.core.management.base import BaseCommand, CommandError
import re
import argparse
from functools import reduce
from operator import or_
import tqdm
from smtplib import SMTPServerDisconnected, SMTPRecipientsRefused

from django.db.models import Q
from django.core.mail import get_connection
from registrations.models import Registration, TicketEvent
from registrations.actions.emails import send_email


class Command(BaseCommand):
    help = "Send tickets to people"

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int)
        parser.add_argument('registration_codes', nargs='*')
        parser.add_argument('-i', '--ignore-sent-status', action='store_false', dest='check_sent_status')

    def handle(self, *args, event_id, registration_codes, check_sent_status, **options):
        try:
            TicketEvent.objects.get(id=event_id)
        except TicketEvent.DoesNotExist:
            raise CommandError('Event does not exist')

        query = Q()

        if registration_codes:
            query = Q(numero__in=registration_codes)

        if check_sent_status:
            query = query & ~Q(ticket_status=Registration.TICKET_SENT)

        connection = get_connection()

        refused = []

        for elem in tqdm.tqdm(Registration.objects.filter(query), desc='Sending tickets'):
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
            self.stdout.write('Could not send to {} ({})'.format(elem.contact_email, elem.numero))
