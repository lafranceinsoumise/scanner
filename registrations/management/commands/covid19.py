import argparse

from django.core.management import BaseCommand
from django.db.models import Q

from registrations.models import Registration, ScannerAction, ScanSeq


class Command(BaseCommand):
    help = "Contact tracing"

    def add_arguments(self, parser):
        parser.add_argument(
            "registration_id", type=int,
        )
        parser.add_argument(
            "-o",
            "--output",
            type=argparse.FileType(mode="w", encoding="utf-8"),
            dest="output_file",
        )

    def handle(self, *args, registration_id, output_file=None, **options):
        r = Registration.objects.get(pk=registration_id)
        query = None

        print("Entrées dans des salles :")
        for scan_event in r.events.filter(
            point__count=True, type=ScannerAction.TYPE_ENTRANCE
        ):
            scan_seqs = [
                ScanSeq.objects.filter(created__lt=scan_event.time).last(),
                ScanSeq.objects.filter(created__gt=scan_event.time).first(),
            ]
            print(f"{scan_event.point.name} à {scan_event.time.isoformat()}")
            print(
                f"Remises à zéro : {scan_seqs[0].created} et {scan_seqs[1].created}\n"
            )

            q = Q(
                events__point=scan_event.point,
                events__time__gt=scan_seqs[0].created,
                events__time__lt=scan_seqs[1].created,
            )

            if query is not None:
                query = query | q
            else:
                query = q

        if output_file:
            for r in (
                Registration.objects.filter(query)
                .filter(uuid__isnull=False)
                .exclude(_contact_emails="")
                .distinct()
            ):
                output_file.write(str(r.contact_email) + "\n")
        else:
            for r in (
                Registration.objects.filter(query)
                .filter(uuid__isnull=False)
                .exclude(_contact_emails="")
                .distinct()
            ):
                print(str(r.contact_email))
