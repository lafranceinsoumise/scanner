from prometheus_client import Counter
from django.template.backends.django import DjangoTemplates
import base64
from io import BytesIO
import subprocess


ticket_generation_counter = Counter('scanner_tickets_generation', 'Number of ticket generation', ['result'])


class TicketGenerationException(Exception):
    pass


def gen_ticket(registration):
    template = DjangoTemplates.from_string(registration.event.template.open())

    context = {'meta_' + p.property: p.value for p in registration.metas.all()}

    context['numero'] = registration.pk
    context['full_name'] = registration.full_name
    context['gender'] = registration.get_gender_display()
    context['category'] = registration.category.name
    context['contact_email'] = registration.contact_email

    img = registration.qrcode
    img_data = BytesIO()
    img.save(img_data, 'PNG')

    context['qrcode_data'] = base64.b64encode(img_data.getvalue())

    res = template.render(context)

    inkscape = subprocess.Popen(
        ['inkscape', '-f', '/dev/stdin', '--export-area-page', '--without-gui', '--export-pdf', '/dev/stdout'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        output, error = inkscape.communicate(
            input=res.encode('utf8'),
            timeout=5
        )
    except subprocess.TimeoutExpired:
        inkscape.kill()
        inkscape.communicate()
        ticket_generation_counter.labels('timeout').inc()
        raise TicketGenerationException('Timeout')

    if inkscape.returncode:
        ticket_generation_counter.labels('inkscape_error').inc()
        raise TicketGenerationException('Return code: %d' % inkscape.returncode)

    ticket_generation_counter.labels('success').inc()
    return output
