import html2text
import requests
from django.core import mail
from django.utils.text import slugify
from django.conf import settings
from django.template.loader import get_template

from prometheus_client import Counter

from .tickets import gen_ticket

_h = html2text.HTML2Text()
_h.ignore_images = True

email_sent_counter = Counter('scanner_email_sent', 'Number of emails sent')


def send_email(registration, connection=None):
    html_message = requests(registration.event.mosaico_url, params={
        'FULL_NAME': registration.full_name,
        **{'META_' + p.property.upper(): p.value for p in registration.metas.all()},
    })
    text_message = _h.handle(html_message)

    if registration.ticket_status == registration.TICKET_MODIFIED:
        subject = registration.event.name + " : modification de votre ticket"
    else:
        subject = registration.event_name + " : votre ticket"

    ticket = gen_ticket(registration)

    email = mail.EmailMultiAlternatives(
        subject=subject,
        from_email=settings.EMAIL_FROM,
        to=[registration.contact_email],
        body=text_message,
        connection=connection,
    )

    email.attach_alternative(html_message, "text/html")
    email.attach(
        filename='ticket_{}.pdf'.format(slugify(registration.full_name)),
        content=ticket,
        mimetype='application/pdf'
    )

    email.send()

    if registration.ticket_status != registration.TICKET_SENT:
        registration.ticket_status = registration.TICKET_SENT
        registration.save()

    email_sent_counter.inc()