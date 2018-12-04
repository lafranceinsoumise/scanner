from rest_framework import serializers

from registrations.models import Registration, RegistrationMeta


class RegistrationMetasField(serializers.DictField):
    child = serializers.CharField(max_length=255)

    def to_representation(self, metas):
        return {meta.property: meta.value for meta in metas.all()}


class RegistrationSerializer(serializers.ModelSerializer):
    metas = RegistrationMetasField()

    def create(self, validated_data):
        metas = validated_data.pop("metas")
        registration = Registration.objects.create(**validated_data)
        for property, value in metas.items():
            RegistrationMeta.objects.create(
                registration=registration, property=property, value=value
            )

        return registration

    def update(self, registration, validated_data):
        metas = validated_data.pop("metas")
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
        fields = ("event", "numero", "category", "ticket_status", "uuid", "metas")
