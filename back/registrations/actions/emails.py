from django.core import mail
from django.utils.text import slugify
from django.template.loader import get_template

from .tickets import gen_ticket


def send_email(registration, connection=None):
    context = {'email': registration.contact_email, 'full_name': registration.full_name}

    body = get_template('registrations/email.txt').render(context)
    html = get_template('registrations/email.html').render(context)

    ticket = gen_ticket(registration)

    email = mail.EmailMultiAlternatives(
        subject='Votre ticket pour la Convention',
        from_email='nepasrepondre@lafranceinsoumise.fr',
        to=[registration.contact_email],
        body=body,
        connection=connection,
    )

    email.attach_alternative(html, "text/html")
    email.attach(
        filename='ticket_{}.pdf'.format(slugify(registration.full_name)),
        content=ticket,
        mimetype='application/pdf'
    )

    email.send()

    if not registration.ticket_sent:
        registration.ticket_sent = True
        registration.save()
