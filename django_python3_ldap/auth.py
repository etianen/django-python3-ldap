"""
Django authentication backend.
"""
from asgiref.sync import sync_to_async
from django.contrib.auth.backends import ModelBackend

from django_python3_ldap import ldap


@sync_to_async
def run_authentication_async(*args, **kwargs):
    """
    Executes the ldap.authenticate function, wrapped in asynchronous execution.
    """
    return ldap.authenticate(*args, **kwargs)


class LDAPBackend(ModelBackend):

    """
    An authentication backend that delegates to an LDAP
    server.

    User models authenticated with LDAP are created on
    the fly, and syncronised with the LDAP credentials.
    """

    supports_inactive_user = False

    def authenticate(self, *args, **kwargs):
        return ldap.authenticate(*args, **kwargs)

    async def aauthenticate(self, *args, **kwargs):
        return await run_authentication_async(*args, **kwargs)
