import html2text
import requests
from django.core import mail
from django.utils.text import slugify
from django.conf import settings

from prometheus_client import Counter

from .tickets import gen_ticket

_h = html2text.HTML2Text()
_h.ignore_images = True

email_sent_counter = Counter("scanner_email_sent", "Number of emails sent")


def send_email(registration, connection=None):
    if registration.ticket_status == registration.TICKET_MODIFIED:
        subject = (
            registration.event.name
            + " : modification du ticket de "
            + registration.full_name
        )
    else:
        subject = registration.event.name + " : ticket de " + registration.full_name

    ticket = gen_ticket(registration)

    for contact_email in registration.contact_emails:
        html_message = requests.get(
            registration.event.mosaico_url,
            params={
                "FULL_NAME": registration.full_name,
                "EMAIL": contact_email,
                **{
                    "META_" + p.property.upper(): p.value
                    for p in registration.metas.all()
                },
            },
        ).content.decode()
        text_message = _h.handle(html_message)

        email = mail.EmailMultiAlternatives(
            subject=subject,
            from_email=settings.EMAIL_FROM,
            to=[contact_email],
            body=text_message,
            connection=connection,
        )

        email.attach_alternative(html_message, "text/html")
        email.attach(
            filename="ticket_{}.pdf".format(slugify(registration.full_name)),
            content=ticket,
            mimetype="application/pdf",
        )

        for attachment in registration.attachments.all():
            with attachment.file.open("rb") as f:
                content = f.read()

            email.attach(
                filename=attachment.filename,
                content=content,
                mimetype=attachment.mimetype
            )

        email.send()

    if registration.ticket_status != registration.TICKET_SENT:
        registration.ticket_status = registration.TICKET_SENT
        registration.save()

    email_sent_counter.inc()
