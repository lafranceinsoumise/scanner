from prometheus_client import Counter
from django.template import engines
import base64
from io import BytesIO
import subprocess

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
            "inkscape",
            "-f",
            "/dev/stdin",
            "--export-area-page",
            "--without-gui",
            "--export-pdf",
            "/dev/stdout",
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
    else:
        inkscape.wait(timeout=5)

    if inkscape.returncode:
        ticket_generation_counter.labels("inkscape_error").inc()
        raise TicketGenerationException("Return code: %d" % inkscape.returncode)

    ticket_generation_counter.labels("success").inc()
    return output
