"""
Settings used by django-python3.
"""
import ldap3
import ssl
from django.conf import settings


class LazySetting(object):
    """
    A proxy to a named Django setting.
    """

    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def __get__(self, obj, cls):
        if obj is None:
            return self
        return getattr(obj._settings, obj.settings_prefix + '_' + self.name, self.default)


class LazySettings(object):
    """
    A proxy to ldap-specific django settings.

    Settings are resolved at runtime, allowing tests
    to change settings at runtime.
    """

    def __init__(self, settings, settings_prefix="LDAP_AUTH"):
        self._settings = settings
        self.settings_prefix = settings_prefix

    LDAP_AUTH_URL = LazySetting(
        name="URL",
        default=["ldap://localhost:389"],
    )

    LDAP_AUTH_USE_TLS = LazySetting(
        name="USE_TLS",
        default=False,
    )

    LDAP_AUTH_TLS_VERSION = LazySetting(
        name="TLS_VERSION",
        default=None,
    )

    LDAP_AUTH_TLS_VALIDATE_CERT = LazySetting(
        name="TLS_VALIDATE_CERT",
        default=ssl.VERIFY_DEFAULT,
    )

    LDAP_AUTH_TLS_LOCAL_CERT_FILE = LazySetting(
        name="TLS_LOCAL_CERT_FILE",
        default=None,
    )

    LDAP_AUTH_TLS_CA_CERTS_FILE = LazySetting(
        name="TLS_CA_CERTS_FILE",
        default=None,
    )

    LDAP_AUTH_TLS_CIPHERS = LazySetting(
        name="TLS_CIPHERS",
        default=None,
    )

    LDAP_AUTH_SEARCH_BASE = LazySetting(
        name="SEARCH_BASE",
        default="ou=people,dc=example,dc=com",
    )

    LDAP_AUTH_OBJECT_CLASS = LazySetting(
        name="OBJECT_CLASS",
        default="inetOrgPerson",
    )

    LDAP_AUTH_USER_FIELDS = LazySetting(
        name="USER_FIELDS",
        default={
            "username": "uid",
            "first_name": "givenName",
            "last_name": "sn",
            "email": "mail",
        },
    )

    LDAP_AUTH_USER_LOOKUP_FIELDS = LazySetting(
        name="USER_LOOKUP_FIELDS",
        default=(
            "username",
        ),
    )

    LDAP_AUTH_CLEAN_USER_DATA = LazySetting(
        name="CLEAN_USER_DATA",
        default="django_python3_ldap.utils.clean_user_data",
    )

    LDAP_AUTH_FORMAT_SEARCH_FILTERS = LazySetting(
        name="FORMAT_SEARCH_FILTERS",
        default="django_python3_ldap.utils.format_search_filters",
    )


    LDAP_AUTH_SYNC_USER_RELATIONS = LazySetting(
        name="SYNC_USER_RELATIONS",
        default="django_python3_ldap.utils.sync_user_relations",
    )

    LDAP_AUTH_FORMAT_USERNAME = LazySetting(
        name="FORMAT_USERNAME",
        default="django_python3_ldap.utils.format_username_openldap",
    )

    LDAP_AUTH_ATTRIBUTES = LazySetting(
        name="ATTRIBUTES",
        default=ldap3.ALL_ATTRIBUTES,
    )

    LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = LazySetting(
        name="ACTIVE_DIRECTORY_DOMAIN",
        default=None,
    )

    LDAP_AUTH_TEST_USER_USERNAME = LazySetting(
        name="TEST_USER_USERNAME",
        default="",
    )

    LDAP_AUTH_TEST_USER_EMAIL = LazySetting(
        name="TEST_USER_EMAIL",
        default=""
    )

    LDAP_AUTH_TEST_USER_PASSWORD = LazySetting(
        name="TEST_USER_PASSWORD",
        default="",
    )

    LDAP_AUTH_CONNECTION_USERNAME = LazySetting(
        name="CONNECTION_USERNAME",
        default=None,
    )

    LDAP_AUTH_CONNECTION_PASSWORD = LazySetting(
        name="CONNECTION_PASSWORD",
        default=None,
    )

    LDAP_AUTH_CONNECT_TIMEOUT = LazySetting(
        name="CONNECT_TIMEOUT",
        default=None
    )

    LDAP_AUTH_RECEIVE_TIMEOUT = LazySetting(
        name="RECEIVE_TIMEOUT",
        default=None
    )


settings = LazySettings(settings)
