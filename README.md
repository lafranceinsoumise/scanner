
# Scanner

Application de scan de billets pour La France Insoumise.

## Dev

Le projet est prévu pour être lancé avec [Lando](https://lando.dev/) (qui
s'appuie sur Docker). Une fois Lando installé, placez-vous à la racine du
projet et lancez :

```bash
cp env.example .env

lando start

# Appliquer les migrations
lando manage migrate

# Créé un nouveau super utilisateur, se souvenir des identifiants, ils seront utilisés pour vous connecter à l'admin
lando manage createsuperuser
```

Vous pouvez ensuite accéder à l'admin via : http://scanner-api.lndo.site/admin/
Et la partie front du scanner via : http://scanner.lndo.site/

### Plus de détails

Lando construit les deux services, installe les dépendances (Poetry côté
Django, npm côté front) et applique les migrations Django automatiquement.

Deux services sont lancés :

1. **django** — la partie backend (Admin Django + API REST).
2. **front** — la partie front du scanner, qui permet aux utilisateurices de
   scanner les billets.

Une fois démarré, les services sont accessibles aux adresses suivantes :

| Service       | URL                              |
| ------------- | -------------------------------- |
| Front scanner | https://scanner.lndo.site        |
| Backend / API | https://scanner-api.lndo.site    |
| Admin Django  | https://scanner-api.lndo.site/admin |

### Commandes utiles

```
lando start          # démarre les services
lando stop           # arrête les services
lando restart        # redémarre les services
lando rebuild        # reconstruit les services (après un changement de dépendances)
lando logs -f        # suit les logs des services

# Commandes Django (via Poetry, dans le service django)
lando ssh -s django                                   # ouvre un shell dans le service
lando manage migrate                        # applique les migrations
lando manage createsuperuser                # crée un compte admin
lando manage <commande>                     # n'importe quelle commande Django
```

> La commande `manage.py` doit être préfixée par `poetry run` si vous l'appelez
> depuis un shell (`lando ssh -s django`). Le raccourci `lando python` ci-dessus
> l'exécute directement dans le bon environnement.

### Base de données

Par défaut, le backend utilise une base SQLite (`db.sqlite3`), suffisante pour
le développement. Aucune configuration supplémentaire n'est nécessaire.
