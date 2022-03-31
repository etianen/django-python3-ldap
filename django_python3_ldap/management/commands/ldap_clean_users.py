from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_python3_ldap import ldap
from django_python3_ldap.conf import settings


class Command(BaseCommand):

    help = "Remove local user models for users not find anymore in the remote LDAP authentication server."

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--purge',
            action='store_true',
            help='Purge instead of deactive local user models'
        )

    def _remove(self, connection, user, purge, verbosity):
        """
        Deactivate or purge a given local user
        """
        if purge:
            # Delete local user
            try:
                user.delete()
                if verbosity >= 1:
                    self.stdout.write("Purged {user}".format(
                        user=user,
                    ))
            except Exception as e:
                raise CommandError("Could not purge user {user}".format(
                    user=user,
                ))
        else:
            # Deactivate local user
            try:
                user.is_active = False
                user.save()
                if verbosity >= 1:
                    self.stdout.write("Deactivated {user}".format(
                        user=user,
                    ))
            except Exception as e:
                raise CommandError("Could not deactivate user {user}".format(
                    user=user,
                ))

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        purge = kwargs.get('purge', False)
        User = get_user_model()
        auth_kwargs = {
            User.USERNAME_FIELD: settings.LDAP_AUTH_CONNECTION_USERNAME,
            'password': settings.LDAP_AUTH_CONNECTION_PASSWORD
        }
        with ldap.connection(**auth_kwargs) as connection:
            if connection is None:
                raise CommandError("Could not connect to LDAP server")
            for user in User.objects.all():
                # For each local users
                # Check if user still exist
                user_kwargs  = {
                    User.USERNAME_FIELD: getattr(user, User.USERNAME_FIELD)
                }
                if connection.has_user(**user_kwargs):
                    continue

                self._remove(connection, user, purge, verbosity)