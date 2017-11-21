# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-21 15:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0003_auto_20171121_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Date et heure'),
        ),
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('scan', 'Scan du code'), ('entrance', 'Entrée sur le site'), ('cancel', 'Annulation après le scan')], max_length=255, verbose_name='Type'),
        ),
    ]