# Generated by Django 2.2.15 on 2020-08-17 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0011_i18n"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="canceled",
            field=models.BooleanField(default=False, verbose_name="Canceled"),
        ),
    ]