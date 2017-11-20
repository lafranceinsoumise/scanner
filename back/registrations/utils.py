import hashlib
import hmac
from base64 import urlsafe_b64decode

from django.conf import settings


def code_is_correct(code):
    (code, userSignature) = code.split('.')
    signature = hmac.new(
        key=settings.SIGNATURE_KEY,
        msg=code.encode('utf-8'),
        digestmod=hashlib.sha1
    ).digest()

    return hmac.compare_digest(signature, urlsafe_b64decode(userSignature))