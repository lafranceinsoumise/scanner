# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-21 19:36
from __future__ import unicode_literals

from django.db import migrations, models
import registrations.actions.tables


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0005_auto_20171121_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='table',
            field=models.CharField(blank=True, max_length=15, validators=[registrations.actions.tables.TableValidator()], verbose_name='Numéro de table'),
        ),
    ]