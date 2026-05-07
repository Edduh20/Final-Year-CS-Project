from pathlib import Path
from decouple import config
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

CORS_ALLOW_ALL_ORIGINS = True

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'titleguard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'titleguard.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool)
    )
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.UserProfile'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'TitleGuard API',
    'DESCRIPTION': 'Land Ownership Management & Verification System',
    'VERSION': '1.0.0',
}

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://localhost:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True


EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='eduumarwa@gmail.com')


ADMIN_EMAIL = config('ADMIN_EMAIL', default='eduumarwa@gmail.com')


MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    
    'USER_ID_FIELD': 'user_id',     
    'USER_ID_CLAIM': 'user_id',
}


KENYA_COUNTIES = [
    ('nairobi', 'Nairobi'),
    ('mombasa', 'Mombasa'),
    ('kwale', 'Kwale'),
    ('kilifi', 'Kilifi'),
    ('tana_river', 'Tana River'),
    ('lamu', 'Lamu'),
    ('taita_taveta', 'Taita Taveta'),
    ('garissa', 'Garissa'),
    ('wajir', 'Wajir'),
    ('mandera', 'Mandera'),
    ('marsabit', 'Marsabit'),
    ('isiolo', 'Isiolo'),
    ('meru', 'Meru'),
    ('tharaka_nithi', 'Tharaka-Nithi'),
    ('embu', 'Embu'),
    ('kitui', 'Kitui'),
    ('machakos', 'Machakos'),
    ('makueni', 'Makueni'),
    ('nyandarua', 'Nyandarua'),
    ('nyeri', 'Nyeri'),
    ('kirinyaga', 'Kirinyaga'),
    ('muranga', 'Murang\'a'),
    ('kiambu', 'Kiambu'),
    ('turkana', 'Turkana'),
    ('west_pokot', 'West Pokot'),
    ('samburu', 'Samburu'),
    ('trans_nzoia', 'Trans Nzoia'),
    ('uasin_gishu', 'Uasin Gishu'),
    ('elgeyo_marakwet', 'Elgeyo-Marakwet'),
    ('nandi', 'Nandi'),
    ('baringo', 'Baringo'),
    ('laikipia', 'Laikipia'),
    ('nakuru', 'Nakuru'),
    ('narok', 'Narok'),
    ('kajiado', 'Kajiado'),
    ('kericho', 'Kericho'),
    ('bomet', 'Bomet'),
    ('kakamega', 'Kakamega'),
    ('vihiga', 'Vihiga'),
    ('bungoma', 'Bungoma'),
    ('busia', 'Busia'),
    ('siaya', 'Siaya'),
    ('kisumu', 'Kisumu'),
    ('homa_bay', 'Homa Bay'),
    ('migori', 'Migori'),
    ('kisii', 'Kisii'),
    ('nyamira', 'Nyamira'),
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

OCR_API_KEY = config("OCR_API_KEY", default=None)