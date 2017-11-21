from django.db import models


class Registration(models.Model):
    TYPE_INVITE = 'invite'
    TYPE_PARTICIPANT = 'participant'
    TYPE_VOLONTAIRE = 'volontaire'
    TYPE_CHOICES = (
        (TYPE_INVITE, 'Invité'),
        (TYPE_PARTICIPANT, 'Participant'),
        (TYPE_VOLONTAIRE, 'Volontaire'),
    )

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER = 'O'
    GENDER_CHOICES = (
        (GENDER_MALE, 'Homme'),
        (GENDER_FEMALE, 'Femme'),
        (GENDER_OTHER, 'Autre / Non défini'),
    )

    numero = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    uuid = models.UUIDField(blank=True, null=True)
    ticket_sent = models.BooleanField(default=False)


class RegistrationMeta(models.Model):
    property = models.CharField(max_length=255)
    value = models.TextField()
    registration = models.ForeignKey('Registration', related_name='metas')


class Event(models.Model):
    TYPE_SCAN = 'scan'
    TYPE_ENTRANCE = 'entrance'
    TYPE_CANCEL = 'cancel'
    TYPE_CHOICES = (
        (TYPE_SCAN, 'Scan du code'),
        (TYPE_ENTRANCE, 'Entrée sur le site'),
        (TYPE_CANCEL, 'Annulation après le scan')
    )

    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    registration = models.ForeignKey('Registration', related_name='events')
    time = models.DateTimeField(auto_now_add=True)