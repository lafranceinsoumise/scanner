# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-21 14:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registration',
            old_name='code',
            new_name='numero',
        ),
    ]