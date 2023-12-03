from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import ProtectedError

from django_python3_ldap import ldap
from django_python3_ldap.utils import group_lookup_args
from django_python3_ldap.utils import get_all_backend_settings


class Command(BaseCommand):
    help = "Remove local user models for users not find anymore in the remote LDAP authentication server."

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--purge',
            action='store_true',
            help='Purge instead of deactive local user models'
        )
        parser.add_argument(
            'lookups',
            nargs='*',
            type=str,
            help='A list of lookup values, matching the fields specified in LDAP_AUTH_USER_LOOKUP_FIELDS. '
                 'If this is not provided then ALL users are concerned.'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Handle superuser (by default, superusers are excluded)'
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Handle staff user (by default,staff users are excluded)'
        )

    def __init__(self, *args, **kwargs):
        self.backends = get_all_backend_settings()
        super().__init__(*args, **kwargs)

    @staticmethod
    def _iter_local_users(User, lookups, superuser, staff):
        """
        Iterates over local users. If the list of lookups is empty, then all users are returned.
        However, if lookups are provided, User.object.get is used to clean each user found using the lookups.
        Exclude or not superuser and or staff user.
        """

        if len(lookups) < 1:
            for user in User.objects.filter(is_superuser=superuser,
                                            is_staff=staff):
                yield user
        else:
            for lookup in group_lookup_args(*lookups):
                try:
                    yield User.objects.get(**lookup,
                                           is_superuser=superuser,
                                           is_staff=staff)
                except User.DoesNotExist:
                    raise CommandError("Could not find user with lookup : {lookup}".format(
                        lookup=lookup,
                    ))

    @staticmethod
    def _remove(user, purge):
        """
        Deactivate or purge a given local user
        """
        if purge:
            # Delete local user
            try:
                user.delete()
            except ProtectedError as e:
                raise CommandError("Could not purge user {user} : {e}".format(
                    user=user,
                    e=e
                ))
        else:
            # Deactivate local user
            user.is_active = False
            user.save()

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        purge = kwargs.get('purge', False)
        lookups = kwargs.get('lookups', [])
        superuser = kwargs.get('superuser', False)
        staff = kwargs.get('staff', False)
        User = get_user_model()

        users_yet_to_identify = set(self._iter_local_users(User, lookups, superuser, staff))

        for backend in self.backends.keys():
            identified_users = self.identify_in_backend(backend, users_yet_to_identify)
            users_yet_to_identify = users_yet_to_identify - identified_users

        for user in users_yet_to_identify:
            # Clean user
            self._remove(user, purge)
            if verbosity >= 1:
                self.stdout.write("{action} {user}".format(
                    action=('Purged' if purge else 'Deactivated'),
                    user=user,
                ))

    def identify_in_backend(self, backend, users):
        """
        Returns a set of users who exist in `backend`.
        """
        identified_users = set()
        settings = self.backends[backend]
        User = get_user_model()

        auth_kwargs = {
            User.USERNAME_FIELD: settings.LDAP_AUTH_CONNECTION_USERNAME,
            'password': settings.LDAP_AUTH_CONNECTION_PASSWORD
        }

        with ldap.connection(settings, **auth_kwargs) as connection:
            if connection is None:
                raise CommandError("Could not connect to LDAP server")
            for user in users:
                # For each local users
                # Check if user still exists
                user_kwargs = {
                    User.USERNAME_FIELD: getattr(user, User.USERNAME_FIELD)
                }
                if connection.has_user(**user_kwargs):
                    identified_users.add(user)

        return identified_users
