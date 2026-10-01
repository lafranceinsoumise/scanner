"""Double authentification (TOTP) optionnelle pour l'admin.

Un utilisateur sans appareil TOTP confirmé se connecte comme avant
(identifiant + mot de passe). S'il a activé la 2FA depuis la page
« Double authentification », le code à 6 chiffres devient obligatoire.
"""

from base64 import b32encode

import qrcode
import qrcode.image.svg
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.forms import AdminAuthenticationForm
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice


def confirmed_device(user):
    return TOTPDevice.objects.filter(user=user, confirmed=True).first()


def check_token(device, token):
    """Vérifie un code en respectant la limitation de tentatives de django-otp."""
    with transaction.atomic():
        allowed, _ = device.verify_is_allowed()
        if not allowed:
            raise forms.ValidationError(
                "Trop de tentatives échouées, réessayez dans quelques instants.",
                code="throttled",
            )
        if not device.verify_token(token):
            raise forms.ValidationError("Code invalide.", code="invalid_token")


class OTPToken(forms.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}
            ),
        )
        super().__init__(max_length=16, **kwargs)

    def clean(self, value):
        return "".join(super().clean(value).split())


class OptionalOTPAdminAuthenticationForm(AdminAuthenticationForm):
    otp_token = OTPToken(
        required=False,
        label="Code de double authentification",
        help_text="Uniquement si vous avez activé la double authentification.",
    )

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        device = confirmed_device(user) if user else None

        if device is not None:
            token = cleaned_data.get("otp_token")
            if not token:
                raise forms.ValidationError(
                    "La double authentification est activée sur ce compte : "
                    "saisissez le code de votre application.",
                    code="token_required",
                )
            check_token(device, token)
            # Persisté en session par django_otp au signal user_logged_in
            user.otp_device = device

        return cleaned_data


class TokenForm(forms.Form):
    otp_token = OTPToken(label="Code à 6 chiffres")

    def __init__(self, *args, device, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device

    def clean_otp_token(self):
        token = self.cleaned_data["otp_token"]
        check_token(self.device, token)
        return token


def qrcode_svg(data):
    image = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=8)
    return mark_safe(image.to_string(encoding="unicode"))


def two_factor_view(request):
    user = request.user
    device = confirmed_device(user)
    enabled = device is not None

    if not enabled:
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        if device is None:
            device = TOTPDevice.objects.create(
                user=user, name="Application d'authentification", confirmed=False
            )

    form = TokenForm(request.POST or None, device=device)

    if request.method == "POST" and form.is_valid():
        if enabled:
            TOTPDevice.objects.filter(user=user).delete()
            messages.success(request, "Double authentification désactivée.")
        else:
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            otp_login(request, device)
            messages.success(request, "Double authentification activée.")
        return redirect("admin:two_factor")

    context = {
        **admin.site.each_context(request),
        "title": "Double authentification",
        "enabled": enabled,
        "form": form,
    }
    if not enabled:
        context["qrcode"] = qrcode_svg(device.config_url)
        context["secret"] = b32encode(device.bin_key).decode()

    return TemplateResponse(request, "admin/two_factor.html", context)
