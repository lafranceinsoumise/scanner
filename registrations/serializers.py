from rest_framework import serializers

from registrations.models import Registration, RegistrationMeta, TicketEvent, ScanPoint


class ScanPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanPoint
        fields = (
            "id",
            "name",
        )


class EventSerializer(serializers.ModelSerializer):
    scan_points = ScanPointSerializer(many=True)

    class Meta:
        model = TicketEvent
        fields = ("name", "scan_points")


class RegistrationMetasField(serializers.DictField):
    child = serializers.CharField(max_length=255)

    def to_representation(self, metas):
        return {meta.property: meta.value for meta in metas.all()}


class RegistrationSerializer(serializers.ModelSerializer):
    metas = RegistrationMetasField()
    contact_email = serializers.EmailField()

    def create(self, validated_data):
        metas = validated_data.pop("metas", {})
        registration = Registration.objects.create(**validated_data)
        for property, value in metas.items():
            RegistrationMeta.objects.create(
                registration=registration, property=property, value=value
            )

        return registration

    def update(self, registration, validated_data):
        metas = validated_data.pop("metas", {})
        result = super().update(registration, validated_data)

        for property, value in metas.items():
            meta, created = RegistrationMeta.objects.get_or_create(
                registration=registration, property=property, defaults={"value": value}
            )
            if not created:
                meta.value = value
                meta.save()

        return result

    class Meta:
        model = Registration
        fields = (
            "id",
            "event",
            "numero",
            "category",
            "ticket_status",
            "full_name",
            "contact_email",
            "gender",
            "uuid",
            "metas",
        )
