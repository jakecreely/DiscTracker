"""
Django settings for disctracker project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the logs directory path
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Create the logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+j)%v)jdbw+#zcz#7bq2vu6nwu$&n_6yo7%dk(8q+c($i64%p8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'items.apps.ItemsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'disctracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "disctracker/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'disctracker.wsgi.application'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": { 
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{", # How the variables will be formatted - { means str.format()
        },
        "simple": {
            "format": "{levelname} {message}", # Outputs the log level and then the message
            "style": "{", # How the string (levelname) and message variable with be formatted - { means str.format()
        },
    },
    "handlers": {
        "console": { # Name of the handler
            "level": "DEBUG", # Handles any logs DEBUG or higher 
            "class": "logging.StreamHandler", # Logs to a stream
            "formatter": "simple", # Uses simple formatter
        },
        "django_file": { # Name of the handler
            "level": "WARNING", # Handles WARNING or higher
            "class": "logging.FileHandler", # Writes logs to a file
            "filename": "logs/django_warnings.log", # Path to log file
            "formatter": "verbose", # Specifies the verbose formatter
        },
        "items_file": { # Name of the handler
            "level": "ERROR", # Handles ERROR or higher
            "class": "logging.FileHandler", # Writes logs to a file
            "filename": "logs/items_errors.log", # Path to log file
            "formatter": "verbose", # Specifies the verbose formatter
        },
    },
    "loggers": {
        "django": { # Generated by django 
            "handlers": ["console", "django_file"], # Handled by both handlers
            "propagate": True,
        },
        "django.requests": { #
            "handlers": ["django_file"], # Outputs to the file handler but not the console
            "level": "ERROR", # Only ERROR or higher
            "propagate": False, # Doesn't propagate to django logger won't handle these errors only this logger will
        },
        "items": {  # Custom logger for items app
            "handlers": ["console", "items_file"], # Logs to both handlers
            "level": "INFO", # Any messages INFO or higher
            "propagate": False, # Doesn't propagate to 
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'disc-tracker',
        'USER': 'username',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
