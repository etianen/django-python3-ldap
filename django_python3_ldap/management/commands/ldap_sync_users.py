from django.core.management.base import BaseCommand
from django.db import transaction

from django_python3_ldap import ldap
from django_python3_ldap.conf import settings


class Command(BaseCommand):

    help = "Creates local user models for all users found in the remote LDAP authentication server."

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        with ldap.connection(**settings.LDAP_AUTH_CONNECTION_KWARGS) as connection:
            for user in connection.iter_users():
                if verbosity >= 1:
                    self.stdout.write("Synced {user}".format(
                        user = user,
                    ))
