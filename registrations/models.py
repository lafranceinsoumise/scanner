from datetime import timezone
import hashlib
import io
import secrets
import subprocess
import logging
from time import strftime, time
import uuid

from django.urls import reverse
from django.db import transaction
from django.core.files.base import ContentFile
from google.oauth2.service_account import Credentials
from google.auth import crypt
import jwt
import json
import os
import tempfile
import zipfile
from OpenSSL import crypto
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.serialization.pkcs7 import PKCS7SignatureBuilder
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.backends import default_backend
import shutil

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.files.storage import default_storage

from .actions.codes import gen_pk_signature_qrcode, gen_qrcode, gen_signed_message

logger = logging.getLogger(__name__)

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
    
    wallet_logo = models.ImageField(
        _("Wallet logo"), upload_to="wallet_logos/", blank=True, null=True,
        help_text=_("Logo used in Google and Apple Wallet passes")
    )
    
    wallet_strip = models.ImageField(
        _("Wallet strip image"), upload_to="wallet_strips/", blank=True, null=True,
        help_text=_("Image used in Apple Wallet passes")
    )
    
    start_date = models.DateTimeField(
        _("Start date"), blank=True, null=True, help_text=_("Event start date")
    )
    end_date = models.DateTimeField(
        _("End date"), blank=True, null=True, help_text=_("Event end date")
    )

    location_name = models.CharField(
        _("Location name"), max_length=255, blank=True, null=True,
        help_text=_("Name of the event location")
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
    
    wallet_token = models.CharField(max_length=32, unique=False, blank=False, null=False)
    
    def generate_unique_token(self):
        for _ in range(5):  # 5 tentatives max
            token = secrets.token_urlsafe(16)
            with transaction.atomic():
                if not Registration.objects.filter(wallet_token=token).exists():
                    return token
        raise ValueError("Could not generate unique token after 5 attempts")

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
    
    wallet_pass = models.FileField(
        upload_to='wallet_passes/',
        null=True,
        blank=True,
        verbose_name="Apple Wallet Pass",
        help_text="Fichier .pkpass généré automatiquement"
    )
    
    @property
    def apple_wallet_url(self):
        self.generate_wallet_pass()
        return reverse('download_pass', kwargs={
            'registration_id': self.pk,
            'token': self.wallet_token
        })

    def generate_wallet_pass(self):
        try:
            # 1. Supprimer l'ancien fichier s'il existe
            if self.wallet_pass:
                try:
                    self.wallet_pass.delete(save=False)
                except:
                    pass
            
            # 2. Générer le contenu
            pkpass_data = self._create_pkpass_file(self._get_pass_data())
            if not pkpass_data:
                raise ValueError("Erreur de génération du fichier .pkpass")
            
            # 3. Chemin relatif de destination
            filename = f"ticket_{self.numero}.pkpass"
            full_path = os.path.join(settings.MEDIA_ROOT, 'wallet_passes', filename)
            
            # 5. Écrire physiquement le fichier
            with open(full_path, 'wb') as f:
                f.write(pkpass_data)
            
            # 6. Lier au modèle
            self.wallet_pass.save(filename, ContentFile(pkpass_data), save=True)
            
            # Double vérification
            if not os.path.exists(full_path):
                raise RuntimeError("Le fichier n'a pas été créé physiquement")
                
        except Exception as e:
            logger.error(f"Erreur critique lors de la génération du pass: {str(e)}")
            raise

    def _get_pass_data(self):
        """Construit les données JSON pour le pass"""
        pass_data = {
            "formatVersion": 1,
            "teamIdentifier": settings.APPLE_TEAM_ID,
            "passTypeIdentifier": settings.APPLE_PASS_TYPE_ID,
            "serialNumber": str(uuid.uuid4()),
            "organizationName": "La France insoumise",
            "relevantDate": self.event.start_date.astimezone(timezone.utc).isoformat(),
            "expirationDate": self.event.end_date.astimezone(timezone.utc).isoformat(),
            "description": f"Billet pour {self.event.name}",
            "eventTicket": {
                "primaryFields": [{
                    "key": "name",
                    "label": "Nom",
                    "value": self.full_name
                }],
                "secondaryFields": [{
                    "key": "location",
                    "label": "Lieu",
                    "value": self.event.location_name
                },
                {
                    "key": "category",
                    "label": "Catégorie",
                    "value": self.category.name
                },
                ],
            },
            "barcode": {
                "format": "PKBarcodeFormatQR",
                "message": gen_pk_signature_qrcode(self.pk),
                "messageEncoding": "utf-8"
            },
            "backgroundColor": "#faebce",
            "logoText": self.event.name,
        }
        
        if self.metas.filter(property="price").exists():
            pass_data["eventTicket"]["auxiliaryFields"] = [{
                "key": "price",
                "label": "Prix",
                "value": self.metas.get(property="price").value
            }]
            
        if self.metas.filter(property="status").exists():
            if self.metas.get(property="status").value == "on-hold":
                pass_data["eventTicket"]["auxiliaryFields"].append({
                    "key": "status",
                    "label": "Statut du paiement",
                    "value": "En attente de paiement"
                })
            elif self.metas.get(property="status").value == "completed":
                pass_data["eventTicket"]["auxiliaryFields"].append({
                    "key": "status",
                    "label": "Statut du paiement",
                    "value": "Paiement terminé"
                })
            
        if self.metas.filter(property="enfant-compagnie").exists():
            pass_data["eventTicket"]["auxiliaryFields"].append({
                "key": "enfant-compagnie",
                "label": "Nombre d'enfants",
                "value": self.metas.get(property="enfant-compagnie").value
            })
            
        if self.metas.filter(property="isMinor").exists() and self.metas.get(property="isMinor").value.lower() == "true":
            pass_data["eventTicket"]["auxiliaryFields"].append({
                "key": "isMinor",
                "label": "Mineur",
                "value": "Oui"
            })
    
        return pass_data

    def _create_pkpass_file(self, pass_data):
        """Crée le fichier .pkpass en mémoire"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Crée pass.json
            with open(os.path.join(temp_dir, "pass.json"), 'w') as f:
                json.dump(pass_data, f)

            # 2. Copie les images
            self._copy_pass_images(temp_dir)

            # 3. Crée manifest.json
            self._create_manifest(temp_dir)

            # 4. Signe le manifest
            self._sign_manifest(temp_dir)

            # 5. Crée l'archive ZIP
            return self._create_zip_archive(temp_dir)

    def _copy_pass_images(self, temp_dir):
        """Copie les images nécessaires pour le pass"""
        if self.event.wallet_logo:
            shutil.copy(self.event.wallet_logo.path, os.path.join(temp_dir, "logo.png"))
            shutil.copy(self.event.wallet_logo.path, os.path.join(temp_dir, "icon.png"))
        
        if self.event.wallet_strip:
            shutil.copy(self.event.wallet_strip.path, os.path.join(temp_dir, "strip.png"))

    def _create_manifest(self, temp_dir):
        """Génère le fichier manifest.json"""
        manifest = {}
        for filename in os.listdir(temp_dir):
            if filename != "manifest.json":
                with open(os.path.join(temp_dir, filename), 'rb') as f:
                    manifest[filename] = hashlib.sha1(f.read()).hexdigest()
        
        with open(os.path.join(temp_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)

    import subprocess

    def _sign_manifest(self, temp_dir):
        try:
            cert_path = settings.APPLE_PASS_CERT_PATH
            password = settings.APPLE_CERTIFICATE_PASSWORD
            
            if not os.path.exists(cert_path):
                raise FileNotFoundError(f"Certificat introuvable : {cert_path}")
            
            # 1. Extraire la clé privée
            subprocess.run([
                "openssl", "pkcs12",
                "-in", cert_path,
                "-nocerts", "-nodes",
                "-passin", f"pass:{password}",
                "-out", os.path.join(temp_dir, "private.key")
            ], check=True)

            # 2. Extraire le certificat
            subprocess.run([
                "openssl", "pkcs12",
                "-in", cert_path,
                "-clcerts", "-nokeys",
                "-passin", f"pass:{password}",
                "-out", os.path.join(temp_dir, "cert.pem")
            ], check=True)

            # 3. Signer le fichier manifest.json
            result = subprocess.run([
                "openssl", "smime", "-binary", "-sign",
                "-certfile", os.path.join(temp_dir, "cert.pem"),
                "-signer", os.path.join(temp_dir, "cert.pem"),
                "-inkey", os.path.join(temp_dir, "private.key"),
                "-in", os.path.join(temp_dir, "manifest.json"),
                "-out", os.path.join(temp_dir, "signature"),
                "-outform", "DER"
            ], check=True)
            
            # delete private key and cert files
            os.remove(os.path.join(temp_dir, "private.key"))
            os.remove(os.path.join(temp_dir, "cert.pem"))
            
            if result.returncode != 0:
                raise ValueError(f"Erreur OpenSSL : {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            error_msg = f"""
            Erreur lors de la signature :
            Sortie: {e.stdout}
            Erreur: {e.stderr}
            """
            logger.error(error_msg)
            raise ValueError("Échec de la signature OpenSSL") from e

    def _create_zip_archive(self, temp_dir):
        """Crée l'archive ZIP en mémoire"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zipf:
            for filename in os.listdir(temp_dir):
                zipf.write(
                    os.path.join(temp_dir, filename),
                    arcname=filename
                )
        return buffer.getvalue()

    def __str__(self):
        return "{} - {} ({})".format(self.numero, self.full_name, self.category.name)
    
    def save(self, *args, **kwargs):
        if not self.wallet_token:
            self.wallet_token = self.generate_unique_token()
        super().save(*args, **kwargs)

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
