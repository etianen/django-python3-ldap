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

    # The LDAP search base for looking up users.
    LDAP_AUTH_SEARCH_BASE = LazySetting(
        name = "LDAP_AUTH_SEARCH_BASE",
        default = "",
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
            "uid" : "username",
            "givenName": "first_name",
            "sn": "last_name",
            "mail": "email",
        },
    )

    # Transforms the user data loaded from
    # LDAP into a form suitable for creating a user.
    LDAP_AUTH_CLEAN_USER_DATA = LazySetting(
        name = "LDAP_AUTH_CLEAN_USER_DATA",
        default = clean_user_data,
    )

    # A tuple of fields that is used to uniquely identify a user.
    LDAP_AUTH_USER_LOOKUP_FIELDS = LazySetting(
        name = "LDAP_AUTH_USER_LOOKUP_FIELDS",
        default = (
            "username",
        ),
    )


settings = LazySettings(settings)
