# Generated by Django 2.2.15 on 2020-08-17 16:42

from django.db import migrations, models
import registrations.models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0010_auto_20200814_1419"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="registration",
            options={
                "verbose_name": "Registration",
                "verbose_name_plural": "Registrations",
            },
        ),
        migrations.AlterModelOptions(
            name="scanpoint",
            options={
                "verbose_name": "Scan point",
                "verbose_name_plural": "Scan points",
            },
        ),
        migrations.AlterModelOptions(
            name="ticketcategory",
            options={
                "verbose_name": "Ticket category",
                "verbose_name_plural": "Ticket categories",
            },
        ),
        migrations.AlterModelOptions(
            name="ticketevent",
            options={
                "ordering": ["-id"],
                "verbose_name": "Event",
                "verbose_name_plural": "Events",
            },
        ),
        migrations.AlterField(
            model_name="registration",
            name="_contact_emails",
            field=models.TextField(blank=True, verbose_name="Contact emails"),
        ),
        migrations.AlterField(
            model_name="registration",
            name="full_name",
            field=models.CharField(max_length=255, verbose_name="Full name"),
        ),
        migrations.AlterField(
            model_name="registration",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("M", "Male"), ("F", "Female"), ("O", "Other / Don't answer")],
                max_length=1,
                verbose_name="Gender",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="numero",
            field=models.CharField(
                max_length=255, null=True, verbose_name="Inscription number"
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="ticket_status",
            field=models.CharField(
                choices=[
                    ("N", "Ticket not sent"),
                    ("M", "Ticket modified since last sending"),
                    ("S", "Updated ticket sent"),
                ],
                default="N",
                max_length=1,
                verbose_name="Ticket status",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="uuid",
            field=models.UUIDField(
                blank=True, null=True, verbose_name="External unique ID"
            ),
        ),
        migrations.AlterField(
            model_name="scanneraction",
            name="person",
            field=models.CharField(max_length=255, verbose_name="Scanning person"),
        ),
        migrations.AlterField(
            model_name="scanneraction",
            name="time",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Date and time"),
        ),
        migrations.AlterField(
            model_name="scanneraction",
            name="type",
            field=models.CharField(
                choices=[
                    ("scan", "QR Code scan"),
                    ("entrance", "Entrance"),
                    ("cancel", "Canceled after scan"),
                ],
                max_length=255,
                verbose_name="Type",
            ),
        ),
        migrations.AlterField(
            model_name="scanpoint",
            name="count",
            field=models.BooleanField(
                default=False, verbose_name="Display ticket count on scan screen"
            ),
        ),
        migrations.AlterField(
            model_name="scanpoint",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Scan point"),
        ),
        migrations.AlterField(
            model_name="scanseq",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, verbose_name="Start of scan sequence"
            ),
        ),
        migrations.AlterField(
            model_name="ticketcategory",
            name="background_color",
            field=models.CharField(max_length=255, verbose_name="Background color"),
        ),
        migrations.AlterField(
            model_name="ticketcategory",
            name="color",
            field=models.CharField(max_length=255, verbose_name="Color"),
        ),
        migrations.AlterField(
            model_name="ticketcategory",
            name="import_key",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Id key in import file"
            ),
        ),
        migrations.AlterField(
            model_name="ticketcategory",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Category name"),
        ),
        migrations.AlterField(
            model_name="ticketevent",
            name="mosaico_url",
            field=models.URLField(blank=True, verbose_name="Email template URL"),
        ),
        migrations.AlterField(
            model_name="ticketevent",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Event name"),
        ),
        migrations.AlterField(
            model_name="ticketevent",
            name="send_tickets_until",
            field=models.DateTimeField(verbose_name="Send tickets until date"),
        ),
        migrations.AlterField(
            model_name="ticketevent",
            name="ticket_template",
            field=models.FileField(
                blank=True,
                upload_to=registrations.models.TicketEvent.get_template_filename,
                verbose_name="Ticket template",
            ),
        ),
    ]