"""
Django authentication backend.
"""

from django.contrib.auth.backends import ModelBackend

from django_python3_ldap import ldap


class LDAPBackend(ModelBackend):

    """
    An authentication backend that delegates to an LDAP
    server.

    User models authenticated with LDAP are created on
    the fly, and syncronised with the LDAP credentials.
    """

    supports_inactive_user = False

    def authenticate(self, *args, **kwargs):
        if hasattr(self, 'PREFIX'):
            kwargs = dict(kwargs, prefix=self.PREFIX)

        return ldap.authenticate(*args, **kwargs)
