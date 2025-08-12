from typing import Optional

from prometheus_client import Counter

from .codes import get_id_from_code, InvalidCodeException
from ..models import Registration, ScannerAction, ScanPoint


scan_counter = Counter("scanner_code_scan", "Numbers of scans", ["result"])
state_change_counter = Counter(
    "scanner_code_state_change", "Numbers of scans", ["result"]
)


def get_registration_from_code(code):
    registration_id = get_id_from_code(code)  # can raise InvalidCodeException
    registration = Registration.objects.get(
        pk=registration_id
    )  # can raise Registration.DoesNotExist
    return registration


def scan_code(code, operator, event, point: Optional[ScanPoint] = None):
    try:
        registration = get_registration_from_code(code)
    except InvalidCodeException:
        scan_counter.labels("invalid_code").inc()
        raise
    except Registration.DoesNotExist:
        scan_counter.labels("missing_code").inc()
        raise InvalidCodeException

    if point is not None and point.event_id != registration.event_id:
        raise InvalidCodeException("wrong_event")

    ScannerAction.objects.create(
        registration=registration,
        type=ScannerAction.TYPE_SCAN,
        person=operator,
        point=point,
    )
    scan_counter.labels("success").inc()
    return registration


def mark_registration(code, type, operator, point=None):
    try:
        registration = get_registration_from_code(code)
    except InvalidCodeException:
        state_change_counter.labels("invalid_code").inc()
        raise
    except Registration.DoesNotExist:
        state_change_counter.labels("missing_code").inc()
        raise InvalidCodeException

    if registration.canceled:
        raise InvalidCodeException("Billet annulé")

    if point is not None and point.event_id != registration.event_id:
        raise InvalidCodeException("wrong_event")

    ScannerAction.objects.create(
        registration=registration, type=type, person=operator, point=point
    )
    state_change_counter.labels(type).inc()
    return registration
