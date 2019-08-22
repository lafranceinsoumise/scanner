import uuid
import argparse
import tqdm
import csv
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q

from registrations.models import (
    Registration,
    RegistrationMeta,
    TicketEvent,
    TicketCategory,
)


def has_attr_changed(obj, attr, value):
    old_value = getattr(obj, attr)

    if value == old_value:
        return False
    else:
        setattr(obj, attr, value)
        return True


def modify_if_changed(
    event_id,
    category,
    properties,
    common_fields,
    meta_fields,
    log_file,
    update_status,
    limit_fields,
):
    # do not use get_or_create ==> we do not want to create empty registration in case something goes wrong
    try:
        registration = Registration.objects.prefetch_related("metas").get(
            event__id=event_id, numero=properties["numero"]
        )
        metas = {m.property: m for m in registration.metas.all()}
        changed = False
    except Registration.DoesNotExist:
        registration = Registration(event_id=event_id, numero=properties["numero"])
        metas = {}
        changed = True
        log_file and log_file.write(
            "New registration: {}\n".format(registration.numero)
        )

    if registration.category_id != category.id:
        registration.category_id = category.id
        changed = True

    for f in common_fields:
        if f == "uuid":
            properties[f] = uuid.UUID(properties[f]) if properties[f] else None
        field_changed = has_attr_changed(registration, f, properties[f])
        changed = changed or field_changed
        if field_changed and log_file:
            log_file.write("Field changed: {} ({})\n".format(f, registration.numero))

    # let's keep only non empty meta properties
    meta_fields = {f for f in meta_fields if properties[f]}
    existing_metas = set(metas)

    # new metas: non empty value that are not in metas dict
    new_metas = meta_fields - existing_metas

    # updated metas: non empty values that are in both meta_fields and metas
    updated_metas = meta_fields & existing_metas

    if limit_fields != []:
        new_metas = new_metas & set(limit_fields)
        updated_metas = updated_metas & set(limit_fields)

    if changed or new_metas or updated_metas:
        with transaction.atomic():
            if changed:
                if (
                    update_status
                    and registration.ticket_status == registration.TICKET_SENT
                ):
                    registration.ticket_status = registration.TICKET_MODIFIED
                registration.save()

            if new_metas:
                for f in new_metas:
                    RegistrationMeta.objects.create(
                        registration_id=registration.id, property=f, value=properties[f]
                    )
                changed = True
                log_file and log_file.write(
                    "New metas: {} ({})\n".format(
                        ", ".join(new_metas), registration.numero
                    )
                )

            for f in updated_metas:
                field_changed = has_attr_changed(metas[f], "value", properties[f])
                changed = changed or field_changed
                if field_changed:
                    metas[f].save()
                    log_file and log_file.write(
                        "Updated meta: {} ({})\n".format(f, registration.numero)
                    )

            if changed:
                if (
                    update_status
                    and registration.ticket_status == registration.TICKET_SENT
                ):
                    registration.ticket_status = registration.TICKET_MODIFIED
                registration.save()
            log_file and log_file.write("Committing\n\n")


class Command(BaseCommand):
    help = "Import people from a CSV"

    def add_arguments(self, parser):
        parser.add_argument("event_id", type=int)
        parser.add_argument(
            "input",
            type=argparse.FileType(mode="r", encoding="utf-8"),
            default=sys.stdin,
            nargs="?",
        )
        parser.add_argument(
            "-l",
            "--log-to",
            type=argparse.FileType(mode="a", encoding="utf-8"),
            dest="log_file",
        )
        parser.add_argument(
            "-n", "--create-only", action="store_true", dest="create_only"
        )
        parser.add_argument(
            "-k", "--keep-status", action="store_false", dest="update_status"
        )
        parser.add_argument(
            "-f", "--fields", action="append", dest="limit_fields", default=[]
        )

    def handle(
        self,
        *args,
        input,
        event_id,
        log_file=None,
        create_only,
        update_status,
        limit_fields,
        **options
    ):
        try:
            TicketEvent.objects.get(id=event_id)
        except TicketEvent.DoesNotExist:
            raise CommandError("Event does not exist")

        r = csv.DictReader(input)

        if any(f not in r.fieldnames for f in ["numero", "category"]):
            raise CommandError(
                "CSV file must have at least columns numero and category"
            )

        if "ticket_status" in r.fieldnames:
            raise CommandError("Ticket status field is not allowed")

        if "contact_email" in r.fieldnames and "contact_emails" in r.fieldnames:
            raise CommandError("contact_email and contact_emails fields are in conflit")

        # read everything so that we import only if full file is valid
        lines = list(r)
        input.close()

        # find columns that are model fields
        model_field_names = {
            "alt_numero",
            "full_name",
            "gender",
            "uuid",
            "contact_email",
            "contact_emails",
        }
        common_fields = (model_field_names & set(r.fieldnames)) - {
            "numero",
            "event",
            "category",
        }
        meta_fields = (
            set(r.fieldnames) - common_fields - {"numero", "event", "category"}
        )

        if limit_fields != []:
            common_fields = common_fields & set(limit_fields)
            meta_fields = meta_fields & set(limit_fields)

        if create_only:
            lines = list(
                line
                for line in lines
                if not Registration.objects.filter(
                    event_id=event_id, numero=line["numero"]
                ).exists()
            )

        # apply validators from field_names
        for field_name in common_fields:
            try:
                field = Registration._meta.get_field(field_name)
            except FieldDoesNotExist:
                field = None

            if field and field.null:
                for line in lines:
                    if not line[field_name]:
                        line[field_name] = None

            if field_name == "contact_emails":
                for line in lines:
                    line["contact_emails"] = line["contact_emails"].split(",")

            try:
                for i, line in enumerate(lines):
                    if line[field_name]:
                        if field:
                            for validator in field.validators:
                                validator(line[field_name])
                        if field_name == "contact_email":
                            validate_email(line[field_name])
                        if field_name == "contact_emails":
                            for contact_email in line[field_name]:
                                validate_email(contact_email)
                    else:
                        if not line[field_name] and (not field or not field.blank):
                            raise CommandError(
                                "Empty value in column %s on line %d"
                                % (field_name, i + 1)
                            )
            except ValidationError:
                raise CommandError(
                    "Incorrect value %s in column %s on line %d"
                    % (line[field_name], field_name, i + 1)
                )

        categories = {}
        for category in {line["category"] for line in lines}:
            try:
                categories[category] = TicketCategory.objects.filter(
                    event_id=event_id
                ).get(Q(name=category) | Q(import_key=category))
            except TicketCategory.DoesNotExist:
                raise CommandError("Category %s does not exist on line %d" % category)

        for line in tqdm.tqdm(lines, desc="Importing"):
            modify_if_changed(
                event_id,
                categories[line["category"]],
                line,
                common_fields,
                meta_fields,
                log_file,
                update_status,
                limit_fields,
            )
