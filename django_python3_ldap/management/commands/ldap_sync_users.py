from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_python3_ldap import ldap
from django.utils.module_loading import import_string
from django_python3_ldap.utils import group_lookup_args, get_all_backend_settings
from django_python3_ldap.auth import LDAPBackend


class Command(BaseCommand):
    help = "Creates local user models for users found in the remote LDAP authentication server."
    backends = None

    def __init__(self, *args, **kwargs):
        self.backends = get_all_backend_settings()
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            'lookups',
            nargs='*',
            help='A list of lookup values, matching the fields specified in LDAP_AUTH_USER_LOOKUP_FIELDS. '
                 'If this is not provided then ALL users are synced.'
        )

        parser.add_argument(
            '--backend',
            action='append',
            default=list(self.backends.keys()) ,
            choices=list(self.backends.keys()),
            help='Limit action to a specific authentication backend instance.\n'
                 'Options include ' + ",".join(self.backends.keys())
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
        backend_names = kwargs.get('backend', None)

        for backend in backend_names:
           settings = self.backends[backend]
           self.do_sync_for_backend(settings, lookups, verbosity)

    def do_sync_for_backend(self, settings, lookups, verbosity):
        User = get_user_model()
        auth_kwargs = {
            User.USERNAME_FIELD: settings.LDAP_AUTH_CONNECTION_USERNAME,
            'password': settings.LDAP_AUTH_CONNECTION_PASSWORD
        }

        with ldap.connection(settings, **auth_kwargs) as connection:
            if connection is None:
                raise CommandError("Could not connect to LDAP server")
            for user in self._iter_synced_users(connection, lookups):
                if verbosity >= 1:
                    self.stdout.write("Synced {user}".format(
                        user=user,
                    ))
