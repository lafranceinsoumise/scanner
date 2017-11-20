from django.db import models


class Registration(models.Model):
    code = models.IntegerField()
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    uuid = models.UUIDField(blank=True, null=True)


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