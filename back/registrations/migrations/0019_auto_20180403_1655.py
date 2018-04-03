# Generated by Django 2.0.4 on 2018-04-03 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0018_auto_20180403_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='numero',
            field=models.CharField(max_length=255, null=True, verbose_name="Numéro d'inscription"),
        ),
        migrations.AlterField(
            model_name='registration',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterUniqueTogether(
            name='registration',
            unique_together={('event', 'numero')},
        ),
    ]
