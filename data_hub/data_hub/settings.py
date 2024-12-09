"""
Django settings for data_hub project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_myjwsv%u@$u7rj(lqcf97-u#6u746hxiletn!24@^213f4cqn'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [os.getenv('ALLOWED_HOST', '0.0.0.0')]


# Application definition

INSTALLED_APPS = [
    'unfold',
    "unfold.contrib.simple_history",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'metadata',
    'tenants',
    'users',
    'acceptance_control',
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

ROOT_URLCONF = 'data_hub.urls'
AUTH_USER_MODEL = "users.CustomUser"

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

WSGI_APPLICATION = 'data_hub.wsgi.application'
LOGIN_REDIRECT_URL = '/metadata/'
LOGOUT_REDIRECT_URL = '/login/'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', "django.db.backends.sqlite3"),
        'NAME': os.environ.get('DATABASE_NAME') if not 'sqlite3' in os.environ.get('DATABASE_ENGINE') else BASE_DIR / 'db.sqlite3',
        'USER': os.environ.get('DATABASE_USER'),
        'PASSWORD': os.environ.get('DATABASE_PASSWD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT')

    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = 'media/'
MEDIA_ROOT = '/media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


UNFOLD = {
    "SITE_HEADER": _("Data Hub"),
    "SITE_TITLE": _("Data Hub"),
    "SITE_SYMBOL": "hub",
    # "SITE_LOGO": {
    #     "light": lambda r: static("wa-logo-green.png"),  # light mode
    #     "dark": lambda r: static("wa-logo-white.png"),  # dark mode
    # },
    # "LOGIN": {
    #     "image": lambda r: static("login-bg.png"),
    #     # "redirect_after": lambda r: reverse_lazy("admin:APP_MODEL_changelist"),
    # },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Navigation"),
                "items": [
                    {
                        "title": _("All Apps"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ]
            },
            {
                "title": _("Tenants"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Tenant"),
                        "icon": 'tenancy',
                        "link": reverse_lazy(
                            "admin:tenants_tenant_changelist"
                        ),
                    },
                    {
                        "title": _("Entity"),
                        "icon": 'fingerprint',
                        "link": reverse_lazy(
                            "admin:tenants_entitytype_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Entity"),
                        "icon": 'type_specimen',
                        "link": reverse_lazy(
                            "admin:tenants_plantentity_changelist"
                        ),
                    },
                    {
                        "title": _("SensorBoxes"),
                        "icon": 'sensors',
                        "link": reverse_lazy(
                            "admin:tenants_sensorbox_changelist"
                        ),
                    },
                ]
            },
            {
                "title": _("Users & Groups"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy(
                            "admin:users_customuser_changelist"
                            ),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy(
                            "admin:auth_group_changelist"
                            ),
                    }
                ],
            },
            {
                "title": _("MetaData"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Languages"),
                        "icon": "language",
                        "link": reverse_lazy(
                            "admin:metadata_language_changelist"
                        ),
                    },
                    {
                        "title": _("Plant Entity Localization"),
                        "icon": "language_international",
                        "link": reverse_lazy(
                            "admin:metadata_plantentitylocalization_changelist"
                        ),
                    },
                    {
                        "title": _("Table Types"),
                        "icon": "data_table",
                        "link": reverse_lazy(
                            "admin:metadata_tabletype_changelist"
                        ),
                    },
                   {
                        "title": _("Data Types"),
                        "icon": "text_fields",
                        "link": reverse_lazy(
                            "admin:metadata_datatype_changelist"
                        ),
                    },
                    {
                        "title": _("Table Fields"),
                        "icon": "view_column",
                        "link": reverse_lazy(
                            "admin:metadata_tablefield_changelist"
                        ),
                    }, 
                    {
                        "title": _("Tenant Table"),
                        "icon": "table_view",
                        "link": reverse_lazy(
                            "admin:metadata_tenanttable_changelist"
                        ),
                    },
                   {
                        "title": _("Field Order"),
                        "icon": "reorder",
                        "link": reverse_lazy(
                            "admin:metadata_fieldorder_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Table Field"),
                        "icon": "table_chart_view",
                        "link": reverse_lazy(
                            "admin:metadata_tenanttablefield_changelist"
                        ),
                    },
                    {
                        "title": _("Table Field Localization"),
                        "icon": "language_international",
                        "link": reverse_lazy(
                            "admin:metadata_tablefieldlocalization_changelist"
                        ),
                    },
                    {
                        "title": _("Table Filter"),
                        "icon": "filter_list",
                        "link": reverse_lazy(
                            "admin:metadata_tablefilter_changelist"
                        ),
                    },
                    {
                        "title": _("Filter Items"),
                        "icon": "category",
                        "link": reverse_lazy(
                            "admin:metadata_filteritem_changelist"
                        ),
                    },
                    {
                        "title": _("Filter Localizations"),
                        "icon": "language_international",
                        "link": reverse_lazy(
                            "admin:metadata_filterlocalization_changelist"
                        ),
                    },
                    {
                        "title": _("Filter Items Localizations"),
                        "icon": "language_international",
                        "link": reverse_lazy(
                            "admin:metadata_filteritemlocalization_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Table Filter"),
                        "icon": "filter_list",
                        "link": reverse_lazy(
                            "admin:metadata_tenanttablefilter_changelist"
                        ),
                    },
                    {
                        "title": _("Table Assets"),
                        "icon": "web_asset",
                        "link": reverse_lazy(
                            "admin:metadata_tableasset_changelist"
                        ),
                    },
                    {
                        "title": _("Table Asset Items"),
                        "icon": "category",
                        "link": reverse_lazy(
                            "admin:metadata_tableassetitem_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Table Assets"),
                        "icon": "device_hub",
                        "link": reverse_lazy(
                            "admin:metadata_tenanttableasset_changelist"
                        ),
                    },
                    {
                        "title": _("ERP Data Types"),
                        "icon": "enterprise",
                        "link": reverse_lazy(
                            "admin:metadata_erpdatatype_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Attachment Requirements"),
                        "icon": "rv_hookup",
                        "link": reverse_lazy(
                            "admin:metadata_tenantattachmentrequirement_changelist"
                        ),
                    },
                    {
                        "title": _("Protocols"),
                        "icon": "sip",
                        "link": reverse_lazy(
                            "admin:metadata_protocol_changelist"
                        ),
                    },
                    {
                        "title": _("Methods"),
                        "icon": "tactic",
                        "link": reverse_lazy(
                            "admin:metadata_method_changelist"
                        ),
                    },
                    {
                        "title": _("Attachment Acquisition Configurations"),
                        "icon": "manufacturing",
                        "link": reverse_lazy(
                            "admin:metadata_attachmentacquisitionconfiguration_changelist"
                        ),
                    },
                    {
                        "title": _("Feedback Forms"),
                        "icon": "feedback",
                        "link": reverse_lazy(
                            "admin:metadata_feedbackform_changelist"
                        ),
                    },
                    {
                        "title": _("Form Fields"),
                        "icon": "input",
                        "link": reverse_lazy(
                            "admin:metadata_formfield_changelist"
                        ),
                    },
                    {
                        "title": _("Feedback Form Fields"),
                        "icon": "description",
                        "link": reverse_lazy(
                            "admin:metadata_feedbackformfield_changelist"
                        ),
                    },
                    {
                        "title": _("Feedback Form Field Items"),
                        "icon": "widgets",
                        "link": reverse_lazy(
                            "admin:metadata_feedbackformfielditem_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Feedback Forms"),
                        "icon": "account_tree",
                        "link": reverse_lazy(
                            "admin:metadata_tenantfeedbackform_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Acceptance Control"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Flag Types"),
                        "icon": "flag",
                        "link": reverse_lazy(
                            "admin:acceptance_control_flagtype_changelist"
                        ),
                    },
                    {
                        "title": _("Flag Types Localization"),
                        "icon": "language_international",
                        "link": reverse_lazy(
                            "admin:acceptance_control_flagtypelocalization_changelist"
                        ),
                    },
                    {
                        "title": _("Severities"),
                        "icon": "grade",
                        "link": reverse_lazy(
                            "admin:acceptance_control_severity_changelist"
                        ),
                    },
                    {
                        "title": _("Tenant Flag Deployment"),
                        "icon": "deployed_code",
                        "link": reverse_lazy(
                            "admin:acceptance_control_tenantflagdeployment_changelist"
                        ),
                    },
                    {
                        "title": _("Deliveries"),
                        "icon": "local_shipping",
                        "link": reverse_lazy(
                            "admin:acceptance_control_delivery_changelist"
                        ),
                    },
                    {
                        "title": _("Delivery Flags"),
                        "icon": "package",
                        "link": reverse_lazy(
                            "admin:acceptance_control_deliveryflag_changelist"
                        ),
                    },
                    {
                        "title": _("Alarm"),
                        "icon": "notifications",
                        "link": reverse_lazy(
                            "admin:acceptance_control_alarm_changelist"
                        ),
                    },
                    {
                        "title": _("Alarm Attributes"),
                        "icon": "edit_attributes",
                        "link": reverse_lazy(
                            "admin:acceptance_control_alarmattr_changelist"
                        ),
                    },
                    {
                        "title": _("Media"),
                        "icon": "play_arrow",
                        "link": reverse_lazy(
                            "admin:acceptance_control_media_changelist"
                        ),
                    },
                    {
                        "title": _("Delivery Media"),
                        "icon": "attach_file",
                        "link": reverse_lazy(
                            "admin:acceptance_control_deliverymedia_changelist"
                        ),
                    },
                    {
                        "title": _("Alarm Media"),
                        "icon": "attach_file",
                        "link": reverse_lazy(
                            "admin:acceptance_control_alarmmedia_changelist"
                        ),
                    },
                    {
                        "title": _("Delivery ERP Attachment"),
                        "icon": "package",
                        "link": reverse_lazy(
                            "admin:acceptance_control_deliveryerpattachment_changelist"
                        ),
                    },
                ]
            }
 
        ],
    },
}
        