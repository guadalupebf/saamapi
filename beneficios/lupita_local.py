# python manage.py shell --settings=api.beneficios.development
# python manage.py runserver --settings=api.beneficios.development

"""
Development settings for Beneficios project.
Remember to:
DJANGO_SETTINGS_MODULE="beneficios.local"
export DJANGO_SETTINGS_MODULE
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from .settings import *
DEBUG = True
#from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.six import python_2_unicode_compatible
# Extra apps for environment
INSTALLED_APPS += (
    'django_extensions',
    'django.contrib.postgres'
)
ALLOWED_HOSTS=['193.168.10.1/8000']
STATIC_ROOT = ''

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases


DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #    'NAME': 'mbx190122026',
       'NAME': 'mbx05022026',
       'USER': 'guadalupe',
       'PASSWORD': 'postgres',
       'HOST': 'localhost',
       'PORT': '5432',
   }
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        #    'rest_framework.permissions.AllowAny',
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',

    ),
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination'
    # 'DEFAULT_RENDERER_CLASSES': [
    #     'rest_framework.renderers.JSONRenderer',
    #     'rest_framework.renderers.AdminRenderer',
    #     'rest_framework.renderers.BrowsableAPIRenderer'
    # ],
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # 'SEARCH_PARAM': 'q',
    # 'PAGINATE_BY': 2,
    # 'PAGINATE_BY_PARAM': 'size',
    # 'MAX_PAGINATE_BY': 8
}


CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = (
    'http://localhost:3000',
    'test.miurabox.com'
)

CORS_ORIGIN_REGEX_WHITELIST = ('^(https?://)?(\w+\.)?miurabox\.com$', )

CORS_ALLOW_HEADERS = (
        'x-requested-with',
        'content-type',
        'accept',
        'origin',
        'authorization',
        'x-csrftoken',
    )

# AMAZON

AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}

AWS_STORAGE_BUCKET_NAME = 'miurabox'
AWS_ACCESS_KEY_ID = 'xxxxx'
AWS_SECRET_ACCESS_KEY = 'xx'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_DEFAULT_ACL = None
MEDIAFILES_LOCATION = 'testing'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


MAILSERVICE = 'http://127.0.0.1:8001/'
# MAILSERVICE = 'https://mail.mbxservicios.com/'
SERVICEEXCEL_URL = 'http://127.0.0.1:8003/'
# SERVICEEXCEL_URL = 'http://report.mbservicios.com/'

# CAS_URL ='http://127.0.0.1:9000/'
CAS_URL ='http://127.0.0.1:9000/'
CAS2_URL ='http://127.0.0.1:9000/'

SERVICEEXCEL_URL ='http://127.0.0.1:8003/'
# SERVICEEXCEL_URL = 'http://report.mbservicios.com/'
SERVICEEXCEL_2_URL ='http://127.0.0.1:8005/'
SERVICEEXCEL_ANCORA_URL='http://127.0.0.1:8005/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'no-reply@miurabox.com'
EMAIL_HOST_PASSWORD = 'xxxxxxxxx'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_L10N = True

USE_TZ = False


JWT_SECRET_KEY = 'CaS2.xxx'
JWT_ALGORITHM = 'HS256'
CAS2_URL = 'http://localhost:9000/'
KEY_CAS = 'xxx'
