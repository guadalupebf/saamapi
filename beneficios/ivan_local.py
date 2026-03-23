from .settings import *


DEBUG = True

# Extra apps for environment
INSTALLED_APPS += (
    'django_extensions',
)

STATIC_ROOT = '/home/xDevelopment/api.beneficios/beneficios/static'

CAS_SERVER_URL = ' http://127.0.0.1:9000/cas/'

CAS_URL ='http://127.0.0.1:9000/'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'saam',
        'USER': 'ivan',
        'PASSWORD': 'postgres',
        'HOST': '',
        'PORT': '',
    }
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


# AMAZON

AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}

AWS_STORAGE_BUCKET_NAME = 'miurabox'
AWS_ACCESS_KEY_ID = 'AKIAJBJ3RBOBIKWSVP3A'
AWS_SECRET_ACCESS_KEY = '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'


AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

MEDIAFILES_LOCATION = 'testing'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'

MAILSERVICE = 'http://mail.mbservicios.com/'




JWT_SECRET_KEY = 'CaS2.0S3cReTk3y'
JWT_ALGORITHM = 'HS256'
CAS2_URL = 'http://localhost:9000/'
KEY_CAS = 'In73RN41K3yCa5'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'no-reply@miurabox.com'
EMAIL_HOST_PASSWORD = 'gvznxkpomzvcmcdu'
