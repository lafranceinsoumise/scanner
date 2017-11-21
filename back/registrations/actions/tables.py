from collections import Counter
from itertools import islice
import random

from django.db.models import Count
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError


def get_random_table():
    from ..models import Registration
    current = Counter(
        {d['table']: d['c'] for d in Registration.objects.values('table').annotate(c=Count('table'))}
    )

    left = settings.TABLE_INFORMATION - current
    total_seats = sum(left.values())
    index = random.randrange(total_seats)

    return next(islice(left.elements(), index, index+1))


@deconstructible
class TableValidator(object):
    def __call__(self, value):
        if value not in settings.TABLE_SET:
            raise ValidationError('Not a correct table name')
