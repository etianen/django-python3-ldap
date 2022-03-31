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

    @staticmethod
    def _remove(user, purge):
        """
        Deactivate or purge a given local user
        """
        if purge:
            # Delete local user
            try:
                user.delete()
            except Exception as e:
                raise CommandError("Could not purge user {user}".format(
                    user=user,
                ))
        else:
            # Deactivate local user
            try:
                user.is_active = False
                user.save()
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
                # Check if user still exists
                user_kwargs  = {
                    User.USERNAME_FIELD: getattr(user, User.USERNAME_FIELD)
                }
                if connection.has_user(**user_kwargs):
                    # User still exists on LDAP side
                    continue
                # Clean user
                self._remove(user, purge)
                if verbosity >= 1:
                    self.stdout.write("{action} {user}".format(
                        action=('Purged' if purge else 'Deactivated'),
                        user=user,
                    ))
