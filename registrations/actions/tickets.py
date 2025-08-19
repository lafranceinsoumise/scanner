from datetime import time, timedelta
from prometheus_client import Counter
from django.template import engines
import base64
from io import BytesIO
import subprocess
from django.utils.timezone import localtime
from django.conf import settings
import pytz
import uuid
import io

from icalendar import Alarm, Calendar, Event

ticket_generation_counter = Counter(
    "scanner_tickets_generation", "Number of ticket generation", ["result"]
)


class TicketGenerationException(Exception):
    pass


def gen_ticket_svg(registration):
    django_engine = engines["django"]
    template = django_engine.from_string(
        registration.event.ticket_template.open().read().decode()
    )

    context = {
        "numero": registration.pk,
        "full_name": registration.full_name,
        "gender": registration.get_gender_display(),
        "category": registration.category.name,
        "contact_email": registration.contact_email,
    }
    context.update({p.property: p.value for p in registration.metas.all()})

    img = registration.qrcode
    img_data = BytesIO()
    img.save(img_data, "PNG")

    context["qrcode_data"] = base64.b64encode(img_data.getvalue()).decode("ascii")

    return template.render(context)

def gen_ticket(registration):
    svg = gen_ticket_svg(registration)

    inkscape = subprocess.Popen(
        [
            "rsvg-convert",
            "--dpi-x=72",
            "--dpi-y=72",
            "--format=pdf",  # format PDF
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        output, error = inkscape.communicate(input=svg.encode("utf8"), timeout=5)
    except subprocess.TimeoutExpired:
        inkscape.kill()
        inkscape.communicate()
        ticket_generation_counter.labels("timeout").inc()
        raise TicketGenerationException("Timeout")

    if inkscape.returncode:
        ticket_generation_counter.labels("inkscape_error").inc()
        raise TicketGenerationException("Return code: %d" % inkscape.returncode)


    gs = subprocess.Popen(
        [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",  # /screen pour + petit, /printer pour meilleure qualité
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            "-sOutputFile=-",
            "-"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    compressed_output, gs_error = gs.communicate(input=output)

    if gs.returncode:
        ticket_generation_counter.labels("gs_error").inc()
        raise TicketGenerationException(f"Ghostscript error: {gs_error.decode()}")

    ticket_generation_counter.labels("success").inc()
    return compressed_output

def gen_event_ics(registration):
    """
    Génère un fichier ICS pour l'événement lié à une registration.
    Retourne le contenu binaire prêt à être envoyé ou sauvegardé.
    """
    event = registration.event

    cal = Calendar()
    cal.add('prodid', '-//LaFranceinsoumise//FR')
    cal.add('version', '2.0')

    ics_event = Event()
    ics_event.add('uid', f"{registration.numero}")
    ics_event.add('summary', event.name)
    ics_event.add('dtstart', localtime(event.start_date))
    ics_event.add('dtend', localtime(event.end_date))
    ics_event.add('dtstamp', localtime(event.start_date))
    ics_event.add('location', event.location_name or "")
    
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', f"Rappel : {event.name}")
    alarm.add('trigger', timedelta(days=-1))  # 1 jour avant
    ics_event.add_component(alarm)

    cal.add_component(ics_event)

    return cal.to_ical()