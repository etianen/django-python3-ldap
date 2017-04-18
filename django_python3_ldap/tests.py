# encoding=utf-8
from __future__ import unicode_literals

from unittest import skipUnless
from io import StringIO, BytesIO

from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.core.management import call_command, CommandError
from django.utils import six

from django_python3_ldap.conf import settings
from django_python3_ldap.ldap import connection
from django_python3_ldap.utils import clean_ldap_name, import_func


@skipUnless(settings.LDAP_AUTH_TEST_USER_USERNAME, "No settings.LDAP_AUTH_TEST_USER_USERNAME supplied.")
@skipUnless(settings.LDAP_AUTH_TEST_USER_PASSWORD, "No settings.LDAP_AUTH_TEST_USER_PASSWORD supplied.")
@skipUnless(settings.LDAP_AUTH_USER_LOOKUP_FIELDS == ("username",), "Cannot test using custom lookup fields.")
@skipUnless(django_settings.AUTH_USER_MODEL == "auth.User", "Cannot test using a custom user model.")
class TestLdap(TestCase):

    def setUp(self):
        super(TestLdap, self).setUp()
        User.objects.all().delete()

    # Lazy settings tests.

    def testLazySettingsInstanceLookup(self):
        self.assertTrue(settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testLazySettingsClassLookup(self):
        self.assertEqual(settings.__class__.LDAP_AUTH_TEST_USER_USERNAME.name, "LDAP_AUTH_TEST_USER_USERNAME")
        self.assertEqual(settings.__class__.LDAP_AUTH_TEST_USER_USERNAME.default, "")

    # Utils tests.

    def testCleanLdapName(self):
        self.assertEqual(clean_ldap_name("foo@bar.com"), r'foo@bar.com')
        self.assertEqual(clean_ldap_name("café"), r'caf\E9')

    # LDAP tests.

    def testGetUserKwargsSuccess(self):
        with connection() as c:
            user = c.get_user(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testGetUserKwargsIncorrectUsername(self):
        with connection() as c:
            user = c.get_user(
                username="bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertEqual(user, None)

    # Authentication tests.

    def testAuthenticateUserSuccess(self):
        user = authenticate(
            username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testAuthenticateUserBadUsername(self):
        user = authenticate(
            username="bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        self.assertEqual(user, None)

    def testAuthenticateUserBadPassword(self):
        user = authenticate(
            username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            password="bad" + settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        self.assertEqual(user, None)

    def testRepeatedUserAuthenticationDoestRecreateUsers(self):
        user_1 = authenticate(
            username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        user_2 = authenticate(
            username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        )
        # Ensure that the user isn't recreated on second access.
        self.assertEqual(user_1.pk, user_2.pk)

    def testAuthenticateWithTLS(self):
        with self.settings(LDAP_AUTH_USE_TLS=True):
            user = authenticate(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testAuthenticateWithRebind(self):
        with self.settings(
            LDAP_AUTH_USE_TLS=True,
            LDAP_AUTH_CONNECTION_USERNAME=settings.LDAP_AUTH_TEST_USER_USERNAME,
            LDAP_AUTH_CONNECTION_PASSWORD=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        ):
            user = authenticate(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
            self.assertIsInstance(user, User)
            self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

    def testAuthenticateWithFailedRebind(self):
        with self.settings(
            LDAP_AUTH_USE_TLS=True,
            LDAP_AUTH_CONNECTION_USERNAME="bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            LDAP_AUTH_CONNECTION_PASSWORD=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        ):
            user = authenticate(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
            self.assertIs(user, None)

    # User synchronisation.

    def testSyncUsersCreatesUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        self.assertGreater(User.objects.count(), 0)

    def testSyncUsersCommandOutput(self):
        out = StringIO() if six.PY3 else BytesIO()
        call_command("ldap_sync_users", verbosity=1, stdout=out)
        rows = out.getvalue().split("\n")[:-1]
        self.assertEqual(len(rows), User.objects.count())
        for row in rows:
            six.assertRegex(self, row, r'^Synced [^\s]+$')

    def testReSyncUsersDoesntRecreateUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        user_count_1 = User.objects.count()
        call_command("ldap_sync_users", verbosity=0)
        user_count_2 = User.objects.count()
        self.assertEqual(user_count_1, user_count_2)

    # User promotion.

    def testPromoteUser(self):
        user = User.objects.create(
            username="test",
        )
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Promote the user.
        call_command("ldap_promote", "test", stdout=StringIO() if six.PY3 else BytesIO())
        user = User.objects.get(username="test")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def testPromoteMissingUser(self):
        with self.assertRaises(CommandError, msg="User with username missing_user does not exist"):
            call_command("ldap_promote", "missing_user", verbosity=0)

    def testSyncUserRelations(self):
        def check_sync_user_relation(user, data):
            # id have been created
            self.assertIsNotNone(user.id)
            # model is saved
            self.assertEqual(user.username, User.objects.get(pk=user.id).username)
            # save all groups
            self.assertIn('cn', data)
            ldap_groups = list(data.get('memberOf', ()))
            ldap_groups.append('default_group')
            for group in ldap_groups:
                user.groups.create(name=group)

        with self.settings(LDAP_AUTH_SYNC_USER_RELATIONS=check_sync_user_relation):
            user = authenticate(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
            self.assertIsInstance(user, User)
            self.assertGreaterEqual(user.groups.count(), 1)
            self.assertEqual(user.groups.filter(name='default_group').count(), 1)

    def testImportFunc(self):
        self.assertIs(clean_ldap_name, import_func(clean_ldap_name))
        self.assertIs(clean_ldap_name, import_func('django_python3_ldap.utils.clean_ldap_name'))
        self.assertTrue(callable(import_func('django.contrib.auth.get_user_model')))

        self.assertRaises(AttributeError, import_func, 123)

        self.assertTrue(callable(import_func(settings.LDAP_AUTH_SYNC_USER_RELATIONS)))

        with self.settings(LDAP_AUTH_SYNC_USER_RELATIONS='django.contrib.auth.get_user_model'):
            self.assertTrue(callable(import_func(settings.LDAP_AUTH_SYNC_USER_RELATIONS)))
