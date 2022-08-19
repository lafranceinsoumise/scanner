# Generated by Django 3.2.6 on 2022-08-19 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0013_ticketattachment"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ticketcategory",
            options={
                "ordering": ("event", "name"),
                "verbose_name": "Ticket category",
                "verbose_name_plural": "Ticket categories",
            },
        ),
        migrations.AddField(
            model_name="ticketcategory",
            name="mosaico_url",
            field=models.URLField(blank=True, verbose_name="Email template URL"),
        ),
    ]
