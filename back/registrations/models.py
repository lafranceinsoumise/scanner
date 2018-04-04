from time import strftime

from django.db import models
from django.utils.text import slugify

from .actions.codes import gen_qrcode

class TicketEvent(models.Model):
    def get_template_filename(instance, filename):
        return strftime(f'templates/{slugify(instance.name)}/%Y-%m-%d-%H-%M.svg')

    name = models.CharField("Nom de l'événement", max_length=255)
    send_tickets_until = models.DateTimeField("Envoyé les tickets jusqu'à la date")
    ticket_template = models.FileField("Template du ticket", upload_to=get_template_filename, blank=True)
    mosaico_url = models.URLField("URL du mail sur Mosaico", blank=True)

    def __str__(self):
        return self.name


class TicketCategory(models.Model):
    name = models.CharField("Nom de la catégorie", max_length=255)
    color = models.CharField("Couleur", max_length=255)
    background_color = models.CharField("Couleur de fond", max_length=255)
    event = models.ForeignKey(TicketEvent, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.event.name})'

    class Meta:
        unique_together = (('event', 'name'),)


class Registration(models.Model):
    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER = 'O'
    GENDER_CHOICES = (
        (GENDER_MALE, 'Homme'),
        (GENDER_FEMALE, 'Femme'),
        (GENDER_OTHER, 'Autre / Non défini'),
    )

    TICKET_NOT_SENT = 'N'
    TICKET_MODIFIED = 'M'
    TICKET_SENT = 'S'
    TICKET_CHOICES = (
        (TICKET_NOT_SENT, "Ticket non envoyé"),
        (TICKET_MODIFIED, "Ticket modifié depuis l'envoi"),
        (TICKET_SENT, "Ticket à jour envoyé")
    )

    event = models.ForeignKey(TicketEvent, on_delete=models.CASCADE)
    numero = models.CharField('Numéro d\'inscription', max_length=255, null=True)
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    contact_email = models.EmailField('Email de contact')
    full_name = models.CharField('Nom complet', max_length=255)
    gender = models.CharField('Genre', max_length=1, choices=GENDER_CHOICES, blank=True)
    uuid = models.UUIDField('Identifiant sur la plateforme', blank=True, null=True)
    ticket_status = models.CharField(
        "Statut du ticket", choices=TICKET_CHOICES, default=TICKET_NOT_SENT, max_length=1, blank=False
    )

    @property
    def qrcode(self):
        return gen_qrcode(self.pk)

    def __str__(self):
        return '{} - {} ({})'.format(self.numero, self.full_name, self.category.name)

    class Meta:
        unique_together = (('event', 'numero'),)


class RegistrationMeta(models.Model):
    property = models.CharField(max_length=255)
    value = models.TextField()
    registration = models.ForeignKey('Registration', related_name='metas', on_delete=models.CASCADE)

    class Meta:
        indexes = (
            models.Index(fields=['registration', 'property'], name='registration_property_index'),
        )


class ScannerAction(models.Model):
    TYPE_SCAN = 'scan'
    TYPE_ENTRANCE = 'entrance'
    TYPE_CANCEL = 'cancel'
    TYPE_CHOICES = (
        (TYPE_SCAN, 'Scan du code'),
        (TYPE_ENTRANCE, 'Entrée sur le site'),
        (TYPE_CANCEL, 'Annulation après le scan')
    )

    type = models.CharField('Type', max_length=255, choices=TYPE_CHOICES)
    registration = models.ForeignKey('Registration', related_name='events', on_delete=models.PROTECT)
    time = models.DateTimeField('Date et heure', auto_now_add=True)
    person = models.CharField('Personne ayant scanné', max_length=255)
