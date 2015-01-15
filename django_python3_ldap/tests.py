from unittest import skipUnless
from io import StringIO

from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.core.management import call_command, CommandError

from django_python3_ldap.conf import settings
from django_python3_ldap.ldap import connection


@skipUnless(settings.LDAP_AUTH_TEST_USER_USERNAME, "No settings.LDAP_AUTH_TEST_USER_USERNAME supplied.")
@skipUnless(settings.LDAP_AUTH_TEST_USER_PASSWORD, "No settings.LDAP_AUTH_TEST_USER_PASSWORD supplied.")
@skipUnless(settings.LDAP_AUTH_USER_LOOKUP_FIELDS == ("username",), "Cannot test using custom lookup fields.")
@skipUnless(django_settings.AUTH_USER_MODEL == "auth.User", "Cannot test using a custom user model.")
class TestLdap(TestCase):

    def setUp(self):
        super().setUp()
        User.objects.all().delete()

    # Lazy settings tests.

    def testLazySettingsInstanceLookup(self):
        self.assertTrue(settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testLazySettingsClassLookup(self):
        self.assertEqual(settings.__class__.LDAP_AUTH_TEST_USER_USERNAME.name, "LDAP_AUTH_TEST_USER_USERNAME")
        self.assertEqual(settings.__class__.LDAP_AUTH_TEST_USER_USERNAME.default, "")

    # LDAP tests.

    def testGetUserArgsSuccess(self):
        with connection() as c:
            user = c.get_user(
                settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testGetUserArgsIncorrectUsername(self):
        with connection() as c:
            user = c.get_user(
                "bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertEqual(user, None)

    def testGetUserArgsExtraField(self):
        with self.assertRaises(TypeError, msg="Expected arguments: username"):
            with connection() as c:
                c.get_user(
                    settings.LDAP_AUTH_TEST_USER_USERNAME,
                    "foo",
                )

    def testGetUserKwargsSuccess(self):
        with connection() as c:
            user = c.get_user(
                username = settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testGetUserKwargsIncorrectUsername(self):
        with connection() as c:
            user = c.get_user(
                username = "bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertEqual(user, None)

    def testGetUserKwrgsExtraField(self):
        with self.assertRaises(TypeError, msg="Expected arguments: username"):
            with connection() as c:
                c.get_user(
                    username = settings.LDAP_AUTH_TEST_USER_USERNAME,
                    foo = "foo",
                )

    def testGetUserBothArgsAndKwargs(self):
        with self.assertRaises(TypeError, msg="Cannot use both args and kwargs to identify a user"):
            with connection() as c:
                c.get_user(
                    settings.LDAP_AUTH_TEST_USER_USERNAME,
                    username = settings.LDAP_AUTH_TEST_USER_USERNAME,
                )

    def testGetUserMissingArgsAndKwargs(self):
        with self.assertRaises(TypeError, msg="Expected arguments: username"):
            with connection() as c:
                c.get_user()

    # Authentication tests.

    def testAuthenticateUserSuccess(self):
        user = authenticate(
            username = settings.LDAP_AUTH_TEST_USER_USERNAME,
            password = settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)
        
    def testAuthenticateUserBadUsername(self):
        user = authenticate(
            username = "bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            password = settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        self.assertEqual(user, None)

    def testAuthenticateUserBadPassword(self):
        user = authenticate(
            username = settings.LDAP_AUTH_TEST_USER_USERNAME,
            password = "bad" + settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        self.assertEqual(user, None)

    def testRepeatedUserAuthenticationDoestRecreateUsers(self):
        user_1 = authenticate(
            username = settings.LDAP_AUTH_TEST_USER_USERNAME,
            password = settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        user_2 = authenticate(
            username = settings.LDAP_AUTH_TEST_USER_USERNAME,
            password = settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        # Ensure that the user isn't recreated on second access.
        self.assertEqual(user_1.pk, user_2.pk)

    # User syncronisation.

    def testSyncUsersCreatesUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        self.assertGreater(User.objects.count(), 0)

    def testSyncUsersCommandOutput(self):
        out = StringIO()
        call_command("ldap_sync_users", verbosity=1, stdout=out)
        rows = out.getvalue().split("\n")[:-1]
        self.assertEqual(len(rows), User.objects.count())
        for row in rows:
            self.assertRegex(row, r'^Synced [^\s]+$')

    def testReSyncUsersDoesntRecreateUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        user_count_1 = User.objects.count()
        call_command("ldap_sync_users", verbosity=0)
        user_count_2 = User.objects.count()
        self.assertEqual(user_count_1, user_count_2)

    # User promotion.

    def testPromoteUser(self):
        user = User.objects.create(
            username = "test",
        )
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Promote the user.
        call_command("ldap_promote", "test", stdout=StringIO())
        user = User.objects.get(username="test")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def testPromoteMissingUser(self):
        with self.assertRaises(CommandError, msg="User with username missing_user does not exist") as cm:
            call_command("ldap_promote", "missing_user", verbosity=0)
