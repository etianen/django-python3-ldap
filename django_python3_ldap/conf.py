"""
Settings used by django-python3.
"""

from django.conf import settings

from django_python3_ldap.utils import clean_user_data


class LazySetting():

    """
    A proxy to a named Django setting.
    """

    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def __get__(self, obj, cls):
        if obj is None:
            return self
        return getattr(obj._settings, self.name, self.default)


class LazySettings():

    """
    A proxy to ldap-specific django settings.

    Settings are resolved at runtime, allowing tests
    to change settings at runtime.
    """

    def __init__(self, settings):
        self._settings = settings

    # The URL of the LDAP server.
    LDAP_AUTH_URL = LazySetting(
        name = "LDAP_AUTH_URL",
        default = "ldap://localhost:389",
    )

    # Initiate TLS on connection.
    LDAP_AUTH_USE_TLS = LazySetting(
        name = "LDAP_AUTH_USE_TLS",
        default = False,
    )

    # The LDAP search base for looking up users.
    LDAP_AUTH_SEARCH_BASE = LazySetting(
        name = "LDAP_AUTH_SEARCH_BASE",
        default = "ou=people,dc=example,dc=com",
    )

    # The LDAP class that represents a user.
    LDAP_AUTH_OBJECT_CLASS = LazySetting(
        name = "LDAP_AUTH_OBJECT_CLASS",
        default = "inetOrgPerson",
    )

    # User model fields mapped to the LDAP
    # attributes that represent them.
    LDAP_AUTH_USER_FIELDS = LazySetting(
        name = "LDAP_AUTH_USER_FIELDS",
        default = {
            "username": "uid",
            "first_name": "givenName",
            "last_name": "sn",
            "email": "mail",
        },
    )

    # A tuple of fields used to uniquely identify a user.
    LDAP_AUTH_USER_LOOKUP_FIELDS = LazySetting(
        name = "LDAP_AUTH_USER_LOOKUP_FIELDS",
        default = (
            "username",
        ),
    )

    # Transforms the user data loaded from
    # LDAP into a form suitable for creating a user.
    LDAP_AUTH_CLEAN_USER_DATA = LazySetting(
        name = "LDAP_AUTH_CLEAN_USER_DATA",
        default = clean_user_data,
    )

    # A username to use when running the live LDAP tests.
    LDAP_AUTH_TEST_USER_USERNAME = LazySetting(
        name = "LDAP_AUTH_TEST_USER_USERNAME",
        default = "",
    )

    # A password to use when running the live LDAP tests.
    LDAP_AUTH_TEST_USER_PASSWORD = LazySetting(
        name = "LDAP_AUTH_TEST_USER_PASSWORD",
        default = "",
    )


settings = LazySettings(settings)
