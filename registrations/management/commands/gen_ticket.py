from django.core.management.base import BaseCommand, CommandError
import argparse

from registrations.models import Registration
from registrations.actions.tickets import gen_ticket


class Command(BaseCommand):
    help = "Generate ticket for given number"

    def add_arguments(self, parser):
        parser.add_argument("registration_id")
        parser.add_argument("output", type=argparse.FileType(mode="wb"))

    def handle(self, *args, registration_id, output, **options):
        registration = Registration.objects.prefetch_related("metas").get(
            pk=registration_id
        )
        ticket = gen_ticket(registration)

        output.write(ticket)
