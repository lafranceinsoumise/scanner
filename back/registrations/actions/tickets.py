from django.template.loader import get_template
from django.conf import settings
import base64
from io import BytesIO
import subprocess


class TicketGenerationException(Exception):
    pass


def gen_ticket(registration):
    template = get_template('registrations/ticket.svg')

    context = {p.property: p.value for p in registration.metas.all()}

    context['numero'] = registration.pk
    context['full_name'] = ' '.join(p for p in [registration.first_name, registration.last_name] if p)
    context['gender'] = registration.get_gender_display()
    context['type'] = registration.get_type_display()
    context['contact_email'] = registration.contact_email
    context['table'] = registration.table
    context['entrance'] = registration.entrance

    if 'transport_type' in context and context['transport_type'] == 'bus':
        context.update(settings.BUS_INFORMATION[context['bus_origin']])

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
        raise TicketGenerationException('Timeout')

    if inkscape.returncode:
        raise TicketGenerationException('Return code: %d' % inkscape.returncode)

    return output
