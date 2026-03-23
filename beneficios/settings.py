import os
import logging.config


LOGGING_CONFIG = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qxxxxxx'

# PARA CONEXION CAS2
JWT_SECRET_KEY = 'CaS2.xxxxxxx'
JWT_ALGORITHM = 'HS256'
NEW_CAS_URL = 'https://test-users.miurabox.com.mx/'


ALLOWED_HOSTS = ['localhost', '127.0.0.1', '45.79.161.222', '.miurabox.com', '10.0.0.201','34.208.67.99','34.208.217.140','10.0.5.70']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'kronos',
    'storages',
    # libs
    'rest_framework',
    'rest_framework.authtoken',
    'django_cas_ng',
    # Modules
    'contratantes',
    'aseguradoras',
    'paquetes',
    'coberturas',
    'contactos',
    'polizas',
    'ramos',
    'recibos',
    'core',
    'generics',
    'forms',
    'organizations',
    'archivos',
    'endorsements',
    'siniestros',
    'claves',
    'fianzas',
    'vendedores',
    'campaigns',
    'endosos',
    'ibis',
    'carpeta',
    'delivery',
    'scripts',
    'control',
    'recordatorios'
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'beneficios.urls'

AUTHENTICATION_BACKENDS = (
    # 'django_cas_ng.backends.CASBackend',
    'django.contrib.auth.backends.ModelBackend',
)


# REST_SESSION_LOGIN = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
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

WSGI_APPLICATION = 'beneficios.wsgi.application'

APIVIEW_ORG_ID = 1


LANGUAGE_CODE = 'es-MX'

TIME_ZONE = 'America/Monterrey'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

# CAS Settings
CAS_VERSION = '3'

# Media Settings
# MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CRONJOBS = [
    ('*/1 * * * *', 'core.views.my_scheduled_job')
]

USER_SOPORTE = 1
SERVICEEXCEL_URL = 'http://report.mbservicios.com/'

SERVICEEXCEL_2_URL = 'https://test-report2.mbservicios.com/'

CAS2_URL = 'https://test-users.miurabox.com.mx/'
KEY_CAS = 'xxx'

CORS_ALLOW_HEADERS = (
        'x-requested-with',
        'content-type',
        'accept',
        'origin',
        'authorization',
        'x-csrftoken',
        'mimeType',
        'responseType'
    )
