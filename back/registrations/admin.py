import hashlib
import hmac
from base64 import urlsafe_b64encode

import qrcode as qrcode
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse

from registrations.models import Registration

class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('qrcode_display',)
    list_filter = ('type',)

    def get_urls(self):
        urls = super().get_urls()
        return [
            url(r'^(.+)/qrcode/$', self.admin_site.admin_view(self.qrcode_view), name='registrations_registration_qrcode')
        ] + urls

    def qrcode_view(self, request, object_id):
        signature = urlsafe_b64encode(hmac.new(
            key=settings.SIGNATURE_KEY,
            msg=str(object_id).encode('utf-8'),
            digestmod=hashlib.sha1
        ).digest())

        img = qrcode.make(str(object_id) + '.' + signature.decode('utf-8'))
        response = HttpResponse(content_type='image/png')
        img.save(response, "PNG")

        return response

    def qrcode_display(self, instance):
        return '<img src="%s"/>' % reverse('admin:registrations_registration_qrcode', args=[instance.code])

    qrcode_display.short_description = 'QRCode'
    qrcode_display.allow_tags = True


admin.site.register(Registration, RegistrationAdmin)
