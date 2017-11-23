from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
import uuid
import argparse
import tqdm
import csv

from registrations.models import Registration, RegistrationMeta
from registrations.actions.tables import get_random_tables


def has_attr_changed(obj, attr, value):
    old_value = getattr(obj, attr)

    if value == old_value:
        return False
    else:
        setattr(obj, attr, value)
        return True


def modify_if_changed(properties, common_fields, meta_fields, assign_table, tables, log_file):
    # do not use get_or_create ==> we do not want to create empty registration in case something goes wrong
    try:
        registration = Registration.objects.prefetch_related('metas').get(numero=properties['numero'])
        metas = {m.property: m for m in registration.metas.all()}
        changed = False
    except Registration.DoesNotExist:
        registration = Registration(numero=properties['numero'])
        metas = {}
        changed = True
        log_file and log_file.write('New registration: {}\n'.format(registration.numero))

    for f in common_fields:
        if f == 'uuid':
            properties[f] = uuid.UUID(properties[f]) if properties[f] else None
        field_changed = has_attr_changed(registration, f, properties[f])
        changed = changed or field_changed
        if field_changed and log_file:
            log_file.write('Field changed: {} ({})\n'.format(f, registration.numero))

    if assign_table and not registration.table:
        if not tables:
            raise CommandError('No more tables to assign !')
        registration.table = tables.pop()
        changed = True
        log_file and log_file.write('Assigned table: {} ({})\n'.format(registration.table, registration.numero))

    # let's keep only non empty meta properties
    meta_fields = {f for f in meta_fields if properties[f]}
    existing_metas = set(metas)

    # new metas: non empty value that are not in metas dict
    new_metas = meta_fields - existing_metas

    # updated metas: non empty values that are in both meta_fields and metas
    updated_metas = meta_fields & existing_metas

    # deleted metas: missing fields and empty fields
    deleted_metas = existing_metas - meta_fields

    with transaction.atomic():
        if new_metas:
            changed = True
            for f in new_metas:
                RegistrationMeta.objects.create(registration=registration, property=f, value=properties[f])
            log_file and log_file.write('New metas: {} ({})\n'.format(', '.join(new_metas), registration.numero))

        if deleted_metas:
            registration.metas.filter(property__in=deleted_metas).delete()
            log_file and log_file.write('Deleted metas: {} ({})\n'.format(', '.join(deleted_metas), registration.numero))

        for f in updated_metas:
            field_changed = has_attr_changed(metas[f], 'value', properties[f])
            changed = changed or field_changed
            if field_changed:
                metas[f].save()
                log_file and log_file.write('Updated meta: {} ({})\n'.format(f, registration.numero))

        if changed:
            if registration.ticket_status == registration.TICKET_SENT:
                registration.ticket_status = registration.TICKET_MODIFIED
            registration.save()
            log_file and log_file.write('Committing\n\n')


class Command(BaseCommand):
    help = "Import people from a CSV"

    def add_arguments(self, parser):
        parser.add_argument('input', type=argparse.FileType(mode='r', encoding='utf-8'))
        parser.add_argument(
            '-a', '--assign-table',
            action='store_true', dest='assign_table'
        )
        parser.add_argument('-l', '--log-to', type=argparse.FileType(mode='a', encoding='utf-8'), dest='log_file')

    def handle(self, *args, input, assign_table, log_file=None, **options):
        r = csv.DictReader(input)

        if any(f not in r.fieldnames for f in ['numero', 'type']):
            raise CommandError('CSV file must have at least columns numero and type')

        if 'ticket_status' in r.fieldnames:
            raise CommandError('Ticket status field is not allowed')

        if assign_table and 'table' in r.fieldnames:
            raise CommandError('Table column in csv file: cannot assign !')

        # read everything so that we import only if full file is valid
        lines = list(r)
        input.close()

        # check numero is good
        for i, line in enumerate(lines):
            if not line['numero'].isdigit():
                raise CommandError('numero field must be an integer on line {}'.format(i+1))

        # find columns that are model fields
        model_field_names = {field.name for field in Registration._meta.get_fields()}
        common_fields = (model_field_names & set(r.fieldnames))- {'numero'}
        meta_fields = set(r.fieldnames) - common_fields - {'numero'}

        # apply validators from field_names
        for field_name in common_fields:
            field = Registration._meta.get_field(field_name)

            if field.null:
                for line in lines:
                    if not line[field_name]:
                        line[field_name] = None

            for validator in field.validators:
                try:
                    for i, line in enumerate(lines):
                        if line[field_name]:
                            validator(line[field_name])
                        else:
                            if not field.blank:
                                raise CommandError('Empty value in column %s on line %d' % (field_name, i+1))
                except ValidationError:
                    raise CommandError('Incorrect value in column %s on line %d' % (field_name, i+1))

        # everything should be ok
        tables = get_random_tables()

        for line in tqdm.tqdm(lines, desc='Importing'):
            modify_if_changed(line, common_fields, meta_fields, assign_table, tables, log_file)
