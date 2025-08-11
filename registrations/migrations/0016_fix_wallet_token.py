# fichier registrations/migrations/0017_fix_wallet_token.py
from django.db import migrations, models
import secrets
from django.db import transaction

def populate_wallet_tokens(apps, schema_editor):
    Registration = apps.get_model('registrations', 'Registration')
    
    for reg in Registration.objects.filter(wallet_token__isnull=True):
        with transaction.atomic():
            for _ in range(5):  # 5 tentatives
                token = secrets.token_urlsafe(16)
                if not Registration.objects.filter(wallet_token=token).exists():
                    reg.wallet_token = token
                    reg.save()
                    break

class Migration(migrations.Migration):
    dependencies = [
        ('registrations', '0015_ticketevent_google_wallet_class_id'),
    ]

    operations = [
        # Étape 1: Ajouter le champ sans unique d'abord
        migrations.AddField(
            model_name='registration',
            name='wallet_token',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        
        # Étape 2: Remplir les tokens de manière unique
        migrations.RunPython(populate_wallet_tokens),
        
        # Étape 3: Modifier le champ en unique
        migrations.AlterField(
            model_name='registration',
            name='wallet_token',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]