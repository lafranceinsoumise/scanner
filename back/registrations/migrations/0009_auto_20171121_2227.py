# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-21 22:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0008_auto_20171121_2027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registration',
            name='ticket_sent',
            field=models.BooleanField(default=False, verbose_name='Ticket envoyé'),
        ),
    ]