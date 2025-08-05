from time import strftime, time

from google.oauth2.service_account import Credentials
from google.auth import crypt
import jwt
import json

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .actions.codes import gen_pk_signature_qrcode, gen_qrcode, gen_signed_message


class TicketEvent(models.Model):
    def get_template_filename(instance, filename):
        return strftime(f"templates/{slugify(instance.name)}/%Y-%m-%d-%H-%M.svg")

    name = models.CharField(_("Event name"), max_length=255)
    send_tickets_until = models.DateTimeField(_("Send tickets until date"))
    ticket_template = models.FileField(
        _("Ticket template"), upload_to=get_template_filename, blank=True
    )
    mosaico_url = models.URLField(_("Email template URL"), blank=True)
    
    google_wallet_class_id = models.CharField(
        _("Google Wallet class ID"), max_length=255, blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-id"]
        verbose_name = _("Event")
        verbose_name_plural = _("Events")


class TicketAttachment(models.Model):
    filename = models.CharField(_("File name"), null=False, blank=False, max_length=60)
    mimetype = models.CharField(_("Mime type"), null=False, blank=False, max_length=100)
    file = models.FileField(_("Attachment"), null=False)
    event = models.ForeignKey(
        TicketEvent,
        on_delete=models.CASCADE,
        related_name="attachments",
        related_query_name="attachment",
    )

    class Meta:
        ordering = ("event", "filename")
        unique_together = ("event", "filename")
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")


class ScanPoint(models.Model):
    event = models.ForeignKey(
        "TicketEvent", related_name="scan_points", on_delete=models.CASCADE
    )
    name = models.CharField(_("Scan point"), max_length=255)
    count = models.BooleanField(_("Display ticket count on scan screen"), default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Scan point")
        verbose_name_plural = _("Scan points")


class ScanSeq(models.Model):
    point = models.ForeignKey(
        "ScanPoint", related_name="seqs", on_delete=models.CASCADE
    )
    created = models.DateTimeField(_("Start of scan sequence"), auto_now_add=True)


class TicketCategory(models.Model):
    import_key = models.CharField(
        _("Id key in import file"), blank=True, max_length=255
    )
    name = models.CharField(_("Category name"), max_length=255)
    color = models.CharField(_("Color"), max_length=255)
    background_color = models.CharField(_("Background color"), max_length=255)
    event = models.ForeignKey(TicketEvent, on_delete=models.CASCADE)
    mosaico_url = models.URLField(_("Email template URL"), blank=True)

    def __str__(self):
        return f"{self.name} ({self.event.name})"

    class Meta:
        unique_together = (("event", "name"),)
        verbose_name = _("Ticket category")
        verbose_name_plural = _("Ticket categories")
        ordering = ("event", "name")


class Registration(models.Model):
    GENDER_MALE = "M"
    GENDER_FEMALE = "F"
    GENDER_OTHER = "O"
    GENDER_CHOICES = (
        (GENDER_MALE, _("Male")),
        (GENDER_FEMALE, _("Female")),
        (GENDER_OTHER, _("Other / Don't answer")),
    )

    TICKET_NOT_SENT = "N"
    TICKET_MODIFIED = "M"
    TICKET_SENT = "S"
    TICKET_CHOICES = (
        (TICKET_NOT_SENT, _("Ticket not sent")),
        (TICKET_MODIFIED, _("Ticket modified since last sending")),
        (TICKET_SENT, _("Updated ticket sent")),
    )

    event = models.ForeignKey(TicketEvent, on_delete=models.CASCADE)
    numero = models.CharField(_("Inscription number"), max_length=255, null=True)
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    _contact_emails = models.TextField(_("Contact emails"), blank=True)
    full_name = models.CharField(_("Full name"), max_length=255)
    gender = models.CharField(
        _("Gender"), max_length=1, choices=GENDER_CHOICES, blank=True
    )
    uuid = models.UUIDField(_("External unique ID"), blank=True, null=True)
    ticket_status = models.CharField(
        _("Ticket status"),
        choices=TICKET_CHOICES,
        default=TICKET_NOT_SENT,
        max_length=1,
        blank=False,
    )

    canceled = models.BooleanField(_("Canceled"), default=False)

    @property
    def contact_email(self):
        return self.contact_emails[0] if self.contact_emails else ""

    @contact_email.setter
    def contact_email(self, value):
        contact_emails = self.contact_emails

        if value in contact_emails:
            contact_emails.pop(contact_emails.index(value))

        contact_emails.insert(0, value)
        self.contact_emails = contact_emails

    @property
    def contact_emails(self):
        return self._contact_emails.split(",") if self._contact_emails else []

    @contact_emails.setter
    def contact_emails(self, value):
        self._contact_emails = ",".join(value)

    @property
    def qrcode(self):
        return gen_qrcode(self.pk)
    
    @property
    def google_wallet_url(self):
        object_payload = {
            "id": f"{settings.GOOGLE_WALLET_USER_ID}.{self.numero}",
            "classId": f"{settings.GOOGLE_WALLET_USER_ID}.{self.event.google_wallet_class_id}",
            "ticketHolderName": self.full_name,
            "ticketNumber": self.numero,
            "eventName": self.event.name,
            "ticketType": {
                "value": self.category.name,
                "language": "fr",
            },
            "reservationInfo": {
                "confirmationCode": self.numero,
            },
            "state": "active" if not self.canceled else "inactive",
            "barcode": {
                "type": "QR_CODE",
                "value": gen_pk_signature_qrcode(self.pk),  # Use the QR code text representation
            },
        }
        
        credentials = Credentials.from_service_account_file(
            settings.GCE_KEY_FILE,
            scopes=["https://www.googleapis.com/auth/wallet_object.issuer"]
        )
        
        with open(settings.GCE_KEY_FILE) as f:
            service_account_info = json.load(f)

        private_key = service_account_info["private_key"]

        # Structure du JWT
        payload = {
            "iss": credentials.service_account_email,
            "aud": "google",
            "typ": "savetowallet",
            "iat": int(time()),
            "payload": {
                "eventTicketObjects": [object_payload]
            }
        }

        token = jwt.encode(payload, private_key, algorithm="RS256")

        return f"https://pay.google.com/gp/v/save/{token}"

    def __str__(self):
        return "{} - {} ({})".format(self.numero, self.full_name, self.category.name)

    class Meta:
        unique_together = (("event", "numero"),)
        verbose_name = _("Registration")
        verbose_name_plural = _("Registrations")


class RegistrationMeta(models.Model):
    property = models.CharField(max_length=255)
    value = models.TextField()
    registration = models.ForeignKey(
        "Registration", related_name="metas", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("registration", "property")


class ScannerAction(models.Model):
    TYPE_SCAN = "scan"
    TYPE_ENTRANCE = "entrance"
    TYPE_CANCEL = "cancel"
    TYPE_CHOICES = (
        (TYPE_SCAN, _("QR Code scan")),
        (TYPE_ENTRANCE, _("Entrance")),
        (TYPE_CANCEL, _("Canceled after scan")),
    )

    type = models.CharField(_("Type"), max_length=255, choices=TYPE_CHOICES)
    registration = models.ForeignKey(
        "Registration", related_name="events", on_delete=models.PROTECT
    )
    point = models.ForeignKey(
        "ScanPoint", related_name="actions", on_delete=models.PROTECT, null=True
    )
    time = models.DateTimeField(_("Date and time"), auto_now_add=True)
    person = models.CharField(_("Scanning person"), max_length=255)

    class Meta:
        ordering = ["-pk"]
