# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-21 17:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0004_auto_20171121_1510'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registration',
            name='last_name',
            field=models.CharField(max_length=255, verbose_name='Nom de famille'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='type',
            field=models.CharField(blank=True, choices=[('invite', 'Invité⋅e'), ('participant', 'Participant⋅e'), ('volontaire', 'Volontaire'), ('volontaire_referent', 'Volontaire référent⋅e'), ('village', 'Village'), ('so', 'Accueil et SO')], max_length=255, verbose_name='Type'),
        ),
        migrations.AddIndex(
            model_name='registrationmeta',
            index=models.Index(fields=['registration', 'property'], name='registration_property_index'),
        ),
    ]