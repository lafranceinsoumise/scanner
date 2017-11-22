from collections import Counter
import random

from django.db.models import Count
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError


def get_random_tables():
    left = settings.TABLE_INFORMATION - get_table_occupation()

    tables = list(left.elements())
    random.shuffle(tables)

    return tables

def get_table_occupation():
    from ..models import Registration
    return Counter(
        {d['table']: d['c'] for d in Registration.objects.values('table').annotate(c=Count('table'))}
    )


@deconstructible
class TableValidator(object):
    def __call__(self, value):
        if value not in settings.TABLE_SET:
            raise ValidationError('Not a correct table name')
