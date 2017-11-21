from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
import re
import argparse
from functools import reduce
from operator import or_
import tqdm

from django.db.models import Q
from registrations.models import Registration
from registrations.actions.emails import send_email


def integer_range(string):
    m = re.match(r'(\d+)(?:-(\d+))?$', string)
    # ^ (or use .split('-'). anyway you like.)
    if not m:
        raise argparse.ArgumentTypeError("'" + string + "' is not a range of number. Expected forms like '0-5' or '2'.")
    start = int(m.group(1))

    if m.group(2):
        return Q(numero__gte=start) & Q(numero__lte=int(m.group(2)))

    return Q(numero=start)


class Command(BaseCommand):
    help = "Send tickets to people"

    def add_arguments(self, parser):
        parser.add_argument('ranges', nargs='+', type=integer_range)
        parser.add_argument('-i', '--ignore-sent-status', action='store_false', dest='check_sent_status')

    def handle(self, *args, ranges, check_sent_status, **options):
        query = reduce(or_, ranges)

        if check_sent_status:
            query = query & Q(ticket_sent=False)

        for elem in tqdm.tqdm(Registration.objects.filter(query)):
            send_email(elem)
