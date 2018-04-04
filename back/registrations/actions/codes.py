import hmac
from base64 import urlsafe_b64encode, urlsafe_b64decode
import binascii
from hashlib import sha1
from django.conf import settings

import qrcode


class InvalidCodeException(Exception):
    pass


def gen_signature(msg):
    return hmac.new(
        key=settings.SIGNATURE_KEY,
        msg=msg,
        digestmod=sha1
    ).digest()


def gen_signed_message(object_id):
    msg = str(object_id).encode('utf8')

    signature = gen_signature(msg)

    return msg + b'.' + urlsafe_b64encode(signature)


def gen_qrcode(object_id):
    full_msg = gen_signed_message(object_id)

    return qrcode.make(full_msg, border=0)


def check_signature(msg, signature):
    correct_signature = gen_signature(msg)
    return hmac.compare_digest(signature, correct_signature)


def get_id_from_code(code):
    """Verify code is correct, and return the identifier if it is. Raise InvalidCodeException if it is not

    The argument is the candidate code as a string. It returns an integer identifier in case of success.
    """

    try:
        identifier, base64_signature = code.split('.')
    except ValueError:
        raise InvalidCodeException('There should be exactly one separator period point')

    try:
        object_id = int(identifier)
    except ValueError:
        raise InvalidCodeException('The identifier should be an integer')

    try:
        signature = urlsafe_b64decode(base64_signature)
    except (binascii.Error, ValueError):
        raise InvalidCodeException('Incorrect base64 signature')

    if not check_signature(identifier.encode('ascii'), signature):
        raise InvalidCodeException('Incorrect signature')

    return object_id
