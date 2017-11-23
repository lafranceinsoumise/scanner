from django.db import models

from .actions.codes import gen_qrcode
from .actions.tables import TableValidator


class Registration(models.Model):
    TYPE_INVITE = 'invite'
    TYPE_PARTICIPANT = 'participant'
    TYPE_VOLONTAIRE = 'volontaire'
    TYPE_VOLONTAIRE_REFERENT = 'volontaire_referent'
    TYPE_VILLAGE = 'village'
    TYPE_ACCUEIL_SO = 'so'
    TYPE_CHOICES = (
        (TYPE_INVITE, 'Invité⋅e'),
        (TYPE_PARTICIPANT, 'Participant⋅e'),
        (TYPE_VOLONTAIRE, 'Volontaire'),
        (TYPE_VOLONTAIRE_REFERENT, 'Volontaire référent⋅e'),
        (TYPE_VILLAGE, 'Village'),
        (TYPE_ACCUEIL_SO, 'Accueil et SO')
    )

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

    numero = models.IntegerField('Numéro', primary_key=True)
    type = models.CharField('Type', max_length=255, choices=TYPE_CHOICES, blank=True)
    contact_email = models.EmailField('Email de contact')
    full_name = models.CharField('Nom complet', max_length=255)
    gender = models.CharField('Genre', max_length=1, choices=GENDER_CHOICES, blank=True)
    uuid = models.UUIDField('Identifiant sur la plateforme', blank=True, null=True)
    ticket_status = models.CharField(
        "Statut du ticket", choices=TICKET_CHOICES, default=TICKET_NOT_SENT, max_length=1, blank=False
    )

    table = models.CharField('Numéro de table', blank=True, max_length=15, validators=[TableValidator()])

    @property
    def entrance(self):
        if self.table:
            zone = self.table[0]

            if zone == '4':
                zone = '2'

            return 'N°{}'.format(zone)
        return ''

    @property
    def qrcode(self):
        return gen_qrcode(self.pk)


class RegistrationMeta(models.Model):
    property = models.CharField(max_length=255)
    value = models.TextField()
    registration = models.ForeignKey('Registration', related_name='metas')

    class Meta:
        indexes = (
            models.Index(['registration', 'property'], name='registration_property_index'),
        )


class Event(models.Model):
    TYPE_SCAN = 'scan'
    TYPE_ENTRANCE = 'entrance'
    TYPE_CANCEL = 'cancel'
    TYPE_CHOICES = (
        (TYPE_SCAN, 'Scan du code'),
        (TYPE_ENTRANCE, 'Entrée sur le site'),
        (TYPE_CANCEL, 'Annulation après le scan')
    )

    type = models.CharField('Type', max_length=255, choices=TYPE_CHOICES)
    registration = models.ForeignKey('Registration', related_name='events')
    time = models.DateTimeField('Date et heure', auto_now_add=True)
    person = models.CharField('Personne ayant scanné', max_length=255)
