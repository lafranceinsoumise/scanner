from django.db.models import Q, Count

from registrations.models import RegistrationMeta


qs = RegistrationMeta.objects.filter(registration__event__id=3, property="table")


# pas plus de 9 par table
assert (
    max(table["nombre"] for table in (qs.values("value").annotate(nombre=Count("*"))))
    == 9
)
# respecter le SO
assert (
    max(
        table["nombre"]
        for table in (
            qs.filter(value__in=["A21", "C25", "D4", "E28"])
            .values("value")
            .annotate(nombre=Count("*"))
        )
    )
    == 7
)

# au moins un nommé correctement inscrit par table
assert (
    min(
        table["nombre"]
        for table in (
            qs.filter()
            .filter(registration__metas__value="nommé")
            .values("value")
            .annotate(nombre=Count("*"))
        )
    )
    == 1
)

# dans le secteur A et C il doit y avoir 9 personnes
assert (
    min(
        table["nombre"]
        for table in (
            qs.filter(
                (Q(value__startswith="A") | Q(value__startswith="C"))
                & ~Q(value="A21")
                & ~Q(value="C25")
            )
            .values("value")
            .annotate(nombre=Count("*"))
        )
    )
    == 9
)


# ailleurs, il peut y avoir 9 personnes uniquement si il y a au moins 2 nommés non inscrit
for table in (
    qs.exclude(Q(value__startswith="A") | Q(value__startswith="C"))
    .values("value")
    .annotate(nombre=Count("*"))
    .filter(nombre__gte=9)
):
    assert qs.filter(value=table["value"], registration__metas__value="nommé").count()
