"""
Django authentication backend.
"""

from django.contrib.auth.backends import ModelBackend

from django_python3_ldap import ldap
from django_python3_ldap.conf import LazySettings
from django.conf import settings

class LDAPBackend(ModelBackend):

    """
    An authentication backend that delegates to an LDAP
    server.

    User models authenticated with LDAP are created on
    the fly, and syncronised with the LDAP credentials.
    """

    supports_inactive_user = False
    settings_prefix = "LDAP_AUTH"

    def authenticate(self, *args, **kwargs):
        prefixed_settings = self.get_settings()
        return ldap.authenticate(*args, settings=prefixed_settings, **kwargs)

    @classmethod
    def get_settings(cls):
        """
        Retrieve settings proxy object based on `settings_prefix`.
        :return: A LazySettings object to be used for authentication.
        """
        return LazySettings(settings, settings_prefix=cls.settings_prefix)