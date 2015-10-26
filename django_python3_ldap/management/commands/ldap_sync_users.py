from django.core.management.base import NoArgsCommand
from django.db import transaction

from django_python3_ldap import ldap
from django_python3_ldap.conf import settings


class Command(NoArgsCommand):

    help = "Creates local user models for all users found in the remote LDAP authentication server."

    @transaction.atomic()
    def handle_noargs(self, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        with ldap.connection(username=settings.LDAP_AUTH_CONNECTION_USERNAME, password=settings.LDAP_AUTH_CONNECTION_PASSWORD) as connection:
            for user in connection.iter_users():
                if verbosity >= 1:
                    self.stdout.write("Synced {user}".format(
                        user = user,
                    ))
