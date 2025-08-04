import base64
import hmac
from base64 import urlsafe_b64encode, urlsafe_b64decode
import binascii
from hashlib import sha1
from django.conf import settings

import qrcode


class InvalidCodeException(Exception):
    pass


def gen_signature(msg):
    return hmac.new(key=settings.SIGNATURE_KEY, msg=msg, digestmod=sha1).digest()


def gen_signed_message(object_id):
    msg = str(object_id).encode("utf8")

    signature = gen_signature(msg)

    return msg + b"." + urlsafe_b64encode(signature)


def gen_qrcode(object_id):
    full_msg = gen_signed_message(object_id)

    return qrcode.make(full_msg, border=0)

def gen_pk_signature_qrcode(object_id: str) -> str:
    msg = str(object_id).encode("utf-8")
    signature = gen_signature(msg)
    b64_signature = urlsafe_b64encode(signature).rstrip(b"=")  # éviter les `=`
    return f"{object_id}.{b64_signature.decode('utf-8')}"

def check_signature(msg, signature):
    correct_signature = gen_signature(msg)
    return hmac.compare_digest(signature, correct_signature)


def get_id_from_code(code):
    """
    Decode and verify code, handling:
    - Wallet format (base64url encoded full 'id.signature')
    - Raw format ('id.signature' plain text)
    Returns the integer identifier if valid.
    Raises InvalidCodeException if invalid.
    """

    def decode_and_split(s):
        try:
            identifier, base64_signature = s.split(".")
        except ValueError:
            raise InvalidCodeException("There should be exactly one separator period point")
        return identifier, base64_signature

    # 1) Essayer de décoder base64url complet (cas Google Wallet)
    try:
        padding = '=' * (-len(code) % 4)
        decoded = urlsafe_b64decode(code + padding).decode('utf-8')
        # Si décodage réussi, on considère que c'est le format Wallet
        identifier, base64_signature = decode_and_split(decoded)
    except (binascii.Error, ValueError):
        # Sinon c'est le format brut
        identifier, base64_signature = decode_and_split(code)

    try:
        object_id = int(identifier)
    except ValueError:
        raise InvalidCodeException("The identifier should be an integer")

    try:
        sig_padding = '=' * (-len(base64_signature) % 4)
        signature = urlsafe_b64decode(base64_signature + sig_padding)
    except (binascii.Error, ValueError):
        raise InvalidCodeException("Incorrect base64 signature")

    if not check_signature(identifier.encode("ascii"), signature):
        raise InvalidCodeException("Incorrect signature")

    return object_id
