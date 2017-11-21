from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
import argparse
import csv
import tqdm

from registrations.models import Registration, RegistrationMeta


class Command(BaseCommand):
    help = "Import people from a CSV"

    def add_arguments(self, parser):
        parser.add_argument('input', type=argparse.FileType(mode='r', encoding='utf-8'))

    def handle(self, *args, input, **options):
        import csv

        r = csv.DictReader(input)

        if any(f not in r.fieldnames for f in ['numero', 'type']):
            raise CommandError('CSV file must have at least columns numero and type')

        if 'ticket_sent' in r.fieldnames:
            raise CommandError('Ticket sent field is not allowed')

        # read everything so that we import only if full file is valid
        lines = list(r)
        input.close()

        # check numero is good
        for i, line in enumerate(lines):
            if not line['numero'].isdigit():
                raise CommandError('numero field must be an integer on line {}'.format(i+1))

        # find columns that are model fields
        model_field_names = {field.name for field in Registration._meta.get_fields()}
        common_fields = (model_field_names & set(r.fieldnames)) - {'numero'}
        meta_fields = set(r.fieldnames) - common_fields

        # apply validators from field_names
        for field_name in common_fields:
            field = Registration._meta.get_field(field_name)
            for validator in field.validators:
                try:
                    for i, line in enumerate(lines):
                        validator(line[field_name])
                except ValidationError:
                    raise CommandError('Incorrect value in column %s on line %d' % (field_name, i+1))

        # everything should be ok
        for line in tqdm.tqdm(lines, desc='Importing'):
            print('Handling')
            registration = Registration.objects.update_or_create(
                numero=line['numero'],
                defaults={field_name: line[field_name] for field_name in common_fields}
            )

            for field_name in meta_fields:
                RegistrationMeta.objects.update_or_create(
                    registration=registration,
                    property=field_name,
                    defaults={'value': line[field_name]}
                )
