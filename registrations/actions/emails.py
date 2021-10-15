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


def envoyer_email(
    recipient, subject, body, html_body=None, connection=None, attachments=None
):
    if attachments is None:
        attachments = []

    msg = mail.EmailMultiAlternatives(
        subject=subject,
        from_email=settings.EMAIL_FROM,
        to=[recipient],
        body=body,
        connection=connection,
    )

    if html_body:
        msg.attach_alternative(html_body, "text/html")

    for filename, content, mime_type in attachments:
        msg.attach(
            filename=filename,
            content=content,
            mimetype=mime_type,
        )

    msg.send()


def envoyer_billet(registration, connection=None):
    if registration.ticket_status == registration.TICKET_MODIFIED:
        subject = (
            registration.event.name
            + " : modification du billet de "
            + registration.full_name
        )
    else:
        subject = registration.event.name + " : billet de " + registration.full_name

    ticket = gen_ticket(registration)

    for contact_email in registration.contact_emails:
        html_message = requests.get(
            registration.event.mosaico_url,
            params={
                "FULL_NAME": registration.full_name,
                "EMAIL": contact_email,
                "CATEGORY": registration.category.name,
                **{
                    "META_" + p.property.upper(): p.value
                    for p in registration.metas.all()
                },
            },
        ).content.decode()
        text_message = _h.handle(html_message)

        attachments = [
            (
                "billet_{}.pdf".format(slugify(registration.full_name)),
                ticket,
                "application/pdf",
            )
        ]

        for attachment in registration.event.attachments.all():
            with attachment.file.open("rb") as f:
                content = f.read()
            attachments.append((attachment.filename, content, attachment.mimetype))

        envoyer_email(
            subject=subject,
            recipient=contact_email,
            body=text_message,
            html_body=html_message,
            attachments=attachments,
            connection=connection,
        )

    if registration.ticket_status != registration.TICKET_SENT:
        registration.ticket_status = registration.TICKET_SENT
        registration.save()

    email_sent_counter.inc()
