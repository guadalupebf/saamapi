from .settings import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk import configure_scope


sentry_sdk.init(
    dsn="https://127551182edd4701bde3b1e5aa4da268@sentry.io/1336223",
    integrations=[DjangoIntegration()],
    send_default_pii = True
)


DEBUG = True

# python manage.py shell --settings=beneficios.production
# python manage.py runserver --settings=beneficios.production

# Extra apps for environment
INSTALLED_APPS += (
  'django_extensions',
  'gunicorn',
  'django.contrib.postgres'
)


CAS_SERVER_URL = ' https://cas.miurabox.com/cas/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mbx_diciembre_18',
        'USER': 'desarrollo',
        'PASSWORD': 'nr5AofZ#Jb4$LiETwJ@s',
        'HOST': 'cp-mbx-info-v1',
        'PORT': '5432',
    }
}

CAS_URL = 'https://cas.miurabox.com/'


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
        'mimeType',
        'responseType'
    )


SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True


# Remember to change this setting to 31536000 seconds

SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        #    'rest_framework.permissions.AllowAny',
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',

    ),
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination'
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    #     'rest_framework.renderers.AdminRenderer',
    #     'rest_framework.renderers.BrowsableAPIRenderer'
    ],
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # 'SEARCH_PARAM': 'q',
    # 'PAGINATE_BY': 2,
    # 'PAGINATE_BY_PARAM': 'size',
    # 'MAX_PAGINATE_BY': 8
}





# AMAZON

AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}

AWS_STORAGE_BUCKET_NAME = 'miurabox'
AWS_ACCESS_KEY_ID = 'xxxx'
AWS_SECRET_ACCESS_KEY = 'xxx'

# Tell django-storages that when coming up with the URL for an item in S3 storage, keep
# it simple - just use this domain plus the path. (If this isn't set, things get complicated).
# This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
# We also use it in the next setting.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_DEFAULT_ACL = None

# This is used by the `static` template tag from `static`, if you're using that. Or if anything else
# refers directly to STATIC_URL. So it's safest to always set it.
# STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN

# Tell the staticfiles app to use S3Boto storage when writing the collected static files (when
# you run `collectstatic`).
# STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

MEDIAFILES_LOCATION = 'testing'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'

#SERVICEEXCEL_URL = 'http://report.mbxservicios.com/'

#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_USE_TLS = True
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'no-reply@miurabox.com'
#EMAIL_HOST_PASSWORD = 'gvznxkpomzvcmcdu'

# Email
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'SG.xxxxxx.x'
EMAIL_USE_TLS = True
# MAILSERVICE = 'https://mail.mbxservicios.com/'

# TIME_ZONE = 'America/Mexico_City'

# USE_I18N = True

# USE_L10N = True

# USE_TZ = False

JWT_SECRET_KEY = 'CaS2.xxxx'
JWT_ALGORITHM = 'HS256'
CAS2_URL = 'https://users-api.miurabox.info/'
KEY_CAS = 'xxxx'
CAS_URL = CAS2_URL

# SERVICEEXCEL_2_URL = 'https://test-report2.mbxservicios.com/'
# SERVICEEXCEL_ANCORA_URL = 'https://report-ancora.miurabox.com/'
MAILSERVICE = 'https://mail-info.mbxservicios.com/'
SERVICEEXCEL_URL = 'https://test-report.mbxservicios.com/'
SERVICEEXCEL_2_URL = 'https://test-report2.mbxservicios.com/'
SERVICEEXCEL_ANCORA_URL = 'https://report-ancora-info.mbxservicios.com/'
