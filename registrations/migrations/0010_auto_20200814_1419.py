# Generated by Django 2.2.14 on 2020-08-14 14:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0009_auto_20200724_1246"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ticketevent", options={"ordering": ["-id"]},
        ),
    ]
