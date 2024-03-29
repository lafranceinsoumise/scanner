"""
Django settings for scanner project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

import dj_email_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET", "1d5a5&y9(220)phk0o9cqjwdpm$3+**d&+kru(2y)!5h-_qn4b"
)
SIGNATURE_KEY = os.environb.get(b"SIGNATURE_KEY", b"prout")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")

CORS_ALLOW_ALL_ORIGINS = DEBUG

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "registrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "scanner.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "scanner.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT")

# Private files
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "media")

email_config = dj_email_url.parse(os.environ.get("SMTP_URL", "smtp://localhost:1025/"))

EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
EMAIL_HOST = email_config["EMAIL_HOST"]
EMAIL_PORT = email_config["EMAIL_PORT"]
EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
EMAIL_USE_TLS = email_config["EMAIL_USE_TLS"]
EMAIL_USE_SSL = email_config["EMAIL_USE_SSL"]

EMAIL_FROM = os.environ.get("EMAIL_FROM", "tickets@lafranceinsoumise.fr")

LOG_DISABLE_JOURNALD = os.environ.get("LOG_DISABLE_JOURNALD", "").lower() in [
    "y",
    "yes",
    "true",
]
if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "journald": {
                "level": "DEBUG",
                "class": "cysystemd.journal.JournaldLogHandler"
                if not LOG_DISABLE_JOURNALD
                else "logging.StreamHandler",
            }
        },
        "loggers": {
            "django.template": {
                "handlers": ["journald"],
                "level": "INFO",
                "propagate": False,
            },
            "django": {"handlers": ["journald"], "level": "DEBUG", "propagate": True},
        },
    }

PROMETHEUS_USER = os.environ.get("PROMETHEUS_USER", "prometheus")
PROMETHEUS_PASSWORD = os.environ.get("PROMETHEUS_PASSWORD", "password")

# DRF
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.DjangoModelPermissions"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}
