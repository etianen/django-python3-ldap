from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model


class Command(BaseCommand):

    help = "Promotes the named users to an admin superuser."

    args = "[username, ...]"

    @transaction.atomic()
    def handle(self, *usernames, **kwargs):
        verbosity = int(kwargs.get("verbosity", 1))
        User = get_user_model()
        for username in usernames:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError("User with username {username} does not exist".format(
                    username = username,
                ))
            else:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                if verbosity >= 1:
                    self.stdout.write("Promoted {user} to admin superuser".format(
                        user = user,
                    ))
