from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_python3_ldap import ldap
from django_python3_ldap.conf import settings
from django.contrib.auth.models import User

class Command(BaseCommand):

    help = "Creates local user models for all users found in the remote LDAP authentication server."

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        with ldap.connection(
            username=settings.LDAP_AUTH_CONNECTION_USERNAME,
            password=settings.LDAP_AUTH_CONNECTION_PASSWORD,
        ) as connection:
            if connection is None:
                raise CommandError("Could not connect to LDAP server")
            user_list = []
            
            for user in connection.iter_users():
                if verbosity >= 1:
                    self.stdout.write("Synced {user}".format(
                        user=user,
                    ))
                    user_list.append(user)
            
            user_difference = list(set(User.objects.all()) - set(user_list))
            print(user_difference)

            for user in user_difference:
                user.is_active = False
                user.save()
                self.stdout.write("Deactivated {user}".format(
                    user=user,
                ))                
            #print(list(connection.user_list()))

