"""
Settings used by django-python3.
"""

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
        return getattr(obj._settings, self.name, self.default)


class LazySettings(object):

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
        default = "django_python3_ldap.utils.clean_user_data",
    )

    # Transforms the user's login information into a form
    # suitable for filtering the user in the LDAP server.
    LDAP_AUTH_CLEAN_SEARCH_DATA = LazySetting(
        name = "LDAP_AUTH_CLEAN_SEARCH_DATA",
        default = "django_python3_ldap.utils.clean_search_data",
    )

    # Callable that can be used to store additional information
    # from LDAP data to user-related models
    LDAP_AUTH_SYNC_USER_RELATIONS = LazySetting(
        name = "LDAP_AUTH_SYNC_USER_RELATIONS",
        default = "django_python3_ldap.utils.sync_user_relations",
    )

    # Formats a user's login information to a form suitable
    # for binding as a username to the LDAP server.
    LDAP_AUTH_FORMAT_USERNAME = LazySetting(
        name = "LDAP_AUTH_FORMAT_USERNAME",
        default = "django_python3_ldap.utils.format_username_openldap",
    )

    # The domain used to authenticate the active directory user.
    # Should be used in combination with
    # LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_active_directory"
    LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = LazySetting(
        name = "LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN",
        default = None,
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

    # A username to perform ldap_sync_users
    LDAP_AUTH_CONNECTION_USERNAME = LazySetting(
        name = "LDAP_AUTH_CONNECTION_USERNAME",
        default = None,
    )

    # A password to perform ldap_sync_users
    LDAP_AUTH_CONNECTION_PASSWORD = LazySetting(
        name = "LDAP_AUTH_CONNECTION_PASSWORD",
        default = None,
    )


settings = LazySettings(settings)
