from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_python3_ldap import ldap
from django_python3_ldap.conf import settings


class Command(BaseCommand):

    help = "Creates local user models for all users found in the remote LDAP authentication server."

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        User = get_user_model()
        auth_kwargs = {
            User.USERNAME_FIELD: settings.LDAP_AUTH_CONNECTION_USERNAME,
            'password': settings.LDAP_AUTH_CONNECTION_PASSWORD
        }
        with ldap.connection(**auth_kwargs) as connection:
            if connection is None:
                raise CommandError("Could not connect to LDAP server")
            for user in connection.iter_users():
                if verbosity >= 1:
                    self.stdout.write("Synced {user}".format(
                        user=user,
                    ))
