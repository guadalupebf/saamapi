from .settings import *

DEBUG = True

# python manage.py shell --settings=beneficios.production
# python manage.py runserver --settings=beneficios.production

# Extra apps for environment
INSTALLED_APPS += (
  'django_extensions',
  'gunicorn',
)


CAS_SERVER_URL = ' https://securitycas.miurabox.com/cas/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'saam',
        'USER': 'security',
        'PASSWORD': 'dsj39jYn5v84spYaMxwjN8an3843848ggzotBnn99993',
        'HOST': '',
        'PORT': '',
    }
}

CAS_URL = 'https://securitycas.miurabox.com/'


CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = (
    'http://localhost',
    'securitycas.miurabox.com',
    'security.miurabox.com',
    'http://localhost'
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


SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True


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
AWS_ACCESS_KEY_ID = 'xxxxxxxxx'
AWS_SECRET_ACCESS_KEY = 'xxxxxxxx'

AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

MEDIAFILES_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'no-reply@miurabox.com'
EMAIL_HOST_PASSWORD = 'xxxxxxx'
