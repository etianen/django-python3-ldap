from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_python3_ldap import ldap
from django_python3_ldap.conf import settings
from django_python3_ldap.utils import group_lookup_args


class Command(BaseCommand):

    help = "Creates local user models for users found in the remote LDAP authentication server."

    def add_arguments(self, parser):
        parser.add_argument(
            'lookups',
            nargs='*',
            type=str,
            help='A list of lookup values, matching the fields specified in LDAP_AUTH_USER_LOOKUP_FIELDS. '
                 'If this is not provided then ALL users are synced.'
        )

    @staticmethod
    def _iter_synced_users(connection, lookups):
        """
        Iterates over synced users. If the list of lookups is empty, then all users are synced using iter_users.
        However, if lookups are provided, get_user is used to sync each user found using the lookups.
        """
        if len(lookups) < 1:
            for user in connection.iter_users():
                yield user
        else:
            for lookup in group_lookup_args(*lookups):
                yield connection.get_user(**lookup)

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        lookups = kwargs.get('lookups', [])
        User = get_user_model()
        auth_kwargs = {
            User.USERNAME_FIELD: settings.LDAP_AUTH_CONNECTION_USERNAME,
            'password': settings.LDAP_AUTH_CONNECTION_PASSWORD
        }
        with ldap.connection(**auth_kwargs) as connection:
            if connection is None:
                raise CommandError("Could not connect to LDAP server")
            for user in self._iter_synced_users(connection, lookups):
                if verbosity >= 1:
                    self.stdout.write("Synced {user}".format(
                        user=user,
                    ))
