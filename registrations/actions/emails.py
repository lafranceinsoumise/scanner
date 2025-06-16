import random
import string
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from io import BytesIO

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

# change email content type to multipart/related to fix img display bugs in some mail clients
class RelatedEmailMultiAlternatives(mail.EmailMultiAlternatives):
    def message(self):
        msg = super().message()
        if msg.is_multipart():
            related_msg = MIMEMultipart(_subtype='related')
            for part in msg.get_payload():
                related_msg.attach(part)
            for k, v in msg.items():
                if k not in related_msg:
                    related_msg[k] = v
            return related_msg
        return msg

def envoyer_email(
    recipient, subject, body, html_body=None, connection=None, attachments=None
):
    if attachments is None:
        attachments = []

    msg = RelatedEmailMultiAlternatives(
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
        template_url = (
            registration.category.mosaico_url or registration.event.mosaico_url
        )

        qr_code_cid = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        html_message = requests.get(
            template_url,
            params={
                "FULL_NAME": registration.full_name,
                "EMAIL": contact_email,
                "CATEGORY": registration.category.name,
                "QR_CODE": f"cid:{qr_code_cid}",
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

        if qr_code_cid in html_message:
            qr_code = BytesIO()
            registration.qrcode.save(qr_code, "PNG")
            attachment = MIMEImage(qr_code.getvalue(), "png")
            attachment.add_header("Content-ID", qr_code_cid)

            attachments.append((
                (attachment, None, None)
            ))

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
