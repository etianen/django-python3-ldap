from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model


class Command(BaseCommand):

    help = "Promotes the named users to an admin superuser."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "usernames",
            metavar="usernames",
            nargs="*",
            help="Usernames to promote to admin superuser.",
        )

    @transaction.atomic()
    def handle(self, **kwargs):
        verbosity = kwargs["verbosity"]
        User = get_user_model()
        for username in kwargs["usernames"]:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError("User with username {username} does not exist".format(
                    username=username,
                ))
            else:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                if verbosity >= 1:
                    self.stdout.write("Promoted {user} to admin superuser".format(
                        user=user,
                    ))
