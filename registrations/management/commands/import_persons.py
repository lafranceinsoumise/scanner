import logging
import uuid
import argparse
from functools import reduce
from operator import or_

import tqdm
import csv
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q, CharField
from django.utils import timezone

from registrations.models import (
    Registration,
    RegistrationMeta,
    TicketEvent,
    ScannerAction,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


REQUIRED_FIELDS = {"numero", "category"}
SPECIAL_FIELDS = {"entry"}


def has_attr_changed(obj, attr, value):
    old_value = getattr(obj, attr)

    if value == old_value:
        return False
    else:
        setattr(obj, attr, value)
        return True


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
        log_file,
        create_only,
        update_status,
        limit_fields,
        **options,
    ):
        verbosity = int(options["verbosity"])

        if verbosity:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter("{levelname} - {message}", style="{")
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(
                {1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}[verbosity]
            )
            logger.addHandler(console_handler)

        if log_file:
            log_file_formatter = logging.Formatter(
                "{asctime} - {levelname} - {message}", style="{"
            )
            log_file_handler = logging.StreamHandler(log_file)
            log_file_handler.setFormatter(log_file_formatter)
            log_file_handler.setLevel(logging.INFO)
            logger.addHandler(log_file_handler)

        try:
            self.event = TicketEvent.objects.get(id=event_id)
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
            "canceled",
            "alt_numero",
            "full_name",
            "gender",
            "uuid",
            "contact_email",
            "contact_emails",
        }
        common_fields = model_field_names & set(r.fieldnames)
        self.meta_fields = (
            set(r.fieldnames) - common_fields - REQUIRED_FIELDS - SPECIAL_FIELDS
        )

        if limit_fields != []:
            common_fields = common_fields & set(limit_fields)
            self.meta_fields = self.meta_fields & set(limit_fields)

        if create_only:
            lines = list(
                line
                for line in lines
                if not Registration.objects.filter(
                    event_id=event_id, numero=line["numero"]
                ).exists()
            )

        self.db_fields = {}
        for field_name in common_fields:
            try:
                self.db_fields[field_name] = Registration._meta.get_field(field_name)
            except FieldDoesNotExist:
                pass

        self.categories = {c.import_key: c for c in self.event.ticketcategory_set.all()}

        for i, line in enumerate(tqdm.tqdm(lines, desc="Importing")):
            if self.validate_line(i, line):
                self.modify_if_changed(
                    line,
                    update_status,
                )

    def validate_line(self, i, line):
        result = True

        if line["category"] not in self.categories:
            logger.error(f"L{i}: catégorie `{line['category']}' inconnue")
            result = False
        else:
            line["category"] = self.categories[line["category"]]

        for field_name, field in self.db_fields.items():
            if field and field.null:
                if not line[field_name]:
                    line[field_name] = None

            if field_name == "contact_emails":
                line["contact_emails"] = line["contact_emails"].split(",")

            if field_name == "uuid":
                try:
                    line["uuid"] = uuid.UUID(line["uuid"]) if line["uuid"] else None
                except ValueError:
                    logger.error("L{i}: uuid invalide")
                    result = False

            if field_name == "canceled":
                line["canceled"] = bool(line["canceled"])

            try:
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
                    if isinstance(field, CharField) and not field.blank:
                        logger.error(f"L{i}: Valeur vide interdite pour {field_name}")
                        result = False
            except ValidationError:
                logger.error(f"L{i}: Valeur incorrecte pour {field_name}")
                result = False

        return result

    def modify_if_changed(
        self,
        properties,
        update_status,
    ):
        # do not use get_or_create ==> we do not want to create empty registration in case something goes wrong
        try:
            registration = Registration.objects.prefetch_related("metas").get(
                event=self.event, numero=properties["numero"]
            )
            metas = {m.property: m for m in registration.metas.all()}
            changed = False
        except Registration.DoesNotExist:
            registration = Registration(
                event=self.event,
                **{
                    k: v
                    for k, v in properties.items()
                    if k in self.db_fields or k in REQUIRED_FIELDS
                },
            )
            metas = {}
            changed = True
            logger.info(f"{registration.numero}: nouveau billet")
        else:
            category = properties["category"]

            if registration.category_id != category.id:
                registration.category_id = category.id
                changed = True
                logger.info(
                    f"{registration.numero}: categorie => `{registration.category.name}'"
                )

            for f in self.db_fields:
                field_changed = has_attr_changed(registration, f, properties[f])
                changed = changed or field_changed
                if field_changed:
                    logger.info(f"{registration.numero}: {f} => {properties[f]}")

        # let's keep only non empty meta properties
        meta_fields = {f for f in self.meta_fields if properties[f]}
        existing_metas = set(metas)

        # new metas: non empty value that are not in metas dict
        new_metas = meta_fields - existing_metas

        # updated metas: non empty values that are in both meta_fields and metas
        if meta_fields & existing_metas:
            updated_metas_cond = reduce(
                or_,
                (
                    Q(registration=registration, property=f) & ~Q(value=properties[f])
                    for f in (meta_fields & existing_metas)
                ),
            )

            updated_metas = set(
                RegistrationMeta.objects.filter(updated_metas_cond).values_list(
                    "property", flat=True
                )
            )
        else:
            updated_metas = set()

        if changed or new_metas or updated_metas:
            if update_status and registration.ticket_status == registration.TICKET_SENT:
                logger.debug(
                    f"{registration.numero}: ticket modifié et prêt à repartir (changed {changed} / new_metas {new_metas} / updated_metas {updated_metas})"
                )
                registration.ticket_status = registration.TICKET_MODIFIED

            registration.save()

            with transaction.atomic():
                if new_metas:
                    for f in new_metas:
                        RegistrationMeta.objects.create(
                            registration_id=registration.id,
                            property=f,
                            value=properties[f],
                        )
                    logger.info(
                        f'{registration.numero}: nouveaux champs: {", ".join(new_metas)}'
                    )

                for f in updated_metas:
                    field_changed = has_attr_changed(metas[f], "value", properties[f])
                    changed = changed or field_changed
                    if field_changed:
                        metas[f].save()
                        logger.info(
                            f"{registration.numero}: champ {f} modifié => `{properties[f]}'"
                        )

        if entry := properties.get("entry", None):
            s, created = ScannerAction.objects.get_or_create(
                registration=registration,
                type=ScannerAction.TYPE_ENTRANCE,
                person="création admin",
                time=timezone.datetime.fromisoformat(entry),
            )
            if created:
                # à cause du auto_add, time est écrasé par la date actuelle
                ScannerAction.objects.filter(id=s.id).update(
                    time=timezone.datetime.fromisoformat(entry)
                )
