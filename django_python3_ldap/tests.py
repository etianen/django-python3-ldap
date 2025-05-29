# encoding=utf-8
from __future__ import unicode_literals

from unittest import skipUnless, skip, mock
from io import StringIO

from asgiref.sync import async_to_sync
from django.test import TestCase, override_settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.core.management import call_command, CommandError

from django_python3_ldap.auth import run_authentication_async
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

    def testHasUserKwargsSuccess(self):
        with connection() as c:
            exist = c.has_user(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertEqual(exist, True)

    def testHasUserKwargsIncorrectUsername(self):
        with connection() as c:
            exist = c.has_user(
                username="bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            )
            self.assertEqual(exist, False)

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

    def testAuthenticateWithAdditonalKwargsUserSuccess(self):
        user = authenticate(
            username=settings.LDAP_AUTH_TEST_USER_USERNAME,
            password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            another_kwarg="whatever",
        )
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, settings.LDAP_AUTH_TEST_USER_USERNAME)

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

    @skip("FIXME: test server currently uses outdated TLS cyphers")
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
            LDAP_AUTH_CONNECTION_USERNAME="bad" + settings.LDAP_AUTH_TEST_USER_USERNAME,
            LDAP_AUTH_CONNECTION_PASSWORD=settings.LDAP_AUTH_TEST_USER_PASSWORD,
        ):
            user = authenticate(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
            self.assertIs(user, None)

    def testAuthenticateWithLimitedRetries(self):
        # simulate offline server
        with self.settings(
            LDAP_AUTH_URL=["ldap://example.com:389"],
            LDAP_AUTH_POOL_ACTIVE=1,
        ):
            user = authenticate(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
        self.assertEqual(user, None)

    def testAuthenticateAsyncRunner(self):
        async_runner = async_to_sync(run_authentication_async)

        with mock.patch("django_python3_ldap.ldap.authenticate") as mocked_authenticate_call:
            async_runner(
                username=settings.LDAP_AUTH_TEST_USER_USERNAME,
                password=settings.LDAP_AUTH_TEST_USER_PASSWORD,
            )
            mocked_authenticate_call.assert_called()

    # User synchronisation.

    def testSyncUsersCreatesUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        self.assertGreater(User.objects.count(), 0)

    def testSyncUserWithLookup(self):
        call_command("ldap_sync_users", settings.LDAP_AUTH_TEST_USER_USERNAME, verbosity=0)
        self.assertEqual(User.objects.filter(username=settings.LDAP_AUTH_TEST_USER_USERNAME).count(), 1)

    @override_settings(LDAP_AUTH_USER_LOOKUP_FIELDS=('username', 'email'))
    def testSyncUserWithMultipleLookups(self):
        call_command(
            "ldap_sync_users",
            settings.LDAP_AUTH_TEST_USER_USERNAME,
            settings.LDAP_AUTH_TEST_USER_EMAIL,
            verbosity=0
        )
        self.assertEqual(User.objects.filter(username=settings.LDAP_AUTH_TEST_USER_USERNAME).count(), 1)

    def testSyncUsersCommandOutput(self):
        out = StringIO()
        call_command("ldap_sync_users", verbosity=1, stdout=out)
        rows = out.getvalue().split("\n")[:-1]
        self.assertEqual(len(rows), User.objects.count())
        for row in rows:
            self.assertRegex(row, r'^Synced ')

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
        call_command("ldap_promote", "test", stdout=StringIO())
        user = User.objects.get(username="test")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def testPromoteMissingUser(self):
        with self.assertRaises(CommandError, msg="User with username missing_user does not exist"):
            call_command("ldap_promote", "missing_user", verbosity=0)

    def testSyncUserRelations(self):
        def check_sync_user_relation(user, data, *, connection=None, dn=None):
            # id have been created
            self.assertIsNotNone(user.id)
            # connection was passed
            self.assertIsNotNone(connection)
            # dn was passed
            self.assertIsNotNone(dn)
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

    def testOldSyncUserRelations(self):
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

    def testCleanUsersDeactivate(self):
        """
        ldap_clean_users management command test
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        _username = "nonldap{user}".format(user=settings.LDAP_AUTH_TEST_USER_USERNAME)
        user = User.objects.create_user(
            _username,
            "nonldap{mail}".format(mail=settings.LDAP_AUTH_TEST_USER_EMAIL),
            settings.LDAP_AUTH_TEST_USER_PASSWORD)
        user.save()
        user_count_1 = User.objects.count()
        self.assertEqual(User.objects.get(username=_username).is_active, True)
        call_command("ldap_clean_users", verbosity=0)
        user_count_2 = User.objects.count()
        self.assertEqual(user_count_1, user_count_2)
        self.assertEqual(User.objects.get(username=_username).is_active, False)

        """
        Test with lookup
        """
        # Reactivate user
        user = User.objects.get(username=_username)
        user.is_active = True
        user.save()
        # Create second user
        _usernameLookup = "nonldaplookup{user}".format(user=settings.LDAP_AUTH_TEST_USER_USERNAME)
        user = User.objects.create_user(
            _usernameLookup,
            "nonldaplookup{mail}".format(mail=settings.LDAP_AUTH_TEST_USER_EMAIL),
            settings.LDAP_AUTH_TEST_USER_PASSWORD)
        user.save()
        user_count_1 = User.objects.count()
        self.assertEqual(User.objects.get(username=_usernameLookup).is_active, True)
        # Clean second user
        call_command("ldap_clean_users", _usernameLookup, verbosity=0)
        user_count_2 = User.objects.count()
        self.assertEqual(user_count_1, user_count_2)
        self.assertEqual(User.objects.get(username=_usernameLookup).is_active, False)
        self.assertEqual(User.objects.get(username=_username).is_active, True)
        # Reactivate second user
        user = User.objects.get(username=_usernameLookup)
        user.is_active = True
        user.save()
        # Clean first user
        call_command("ldap_clean_users", _username, verbosity=0)
        self.assertEqual(User.objects.get(username=_username).is_active, False)
        self.assertEqual(User.objects.get(username=_usernameLookup).is_active, True)
        # Lookup a non existing user (raise a CommandError)
        with self.assertRaises(CommandError):
            call_command("ldap_clean_users", 'doesnonexist', verbosity=0)

        """
        Test with superuser
        """
        # Reactivate first user and promote to superuser
        user = User.objects.get(username=_username)
        user.is_active = True
        user.is_superuser = True
        user.save()
        # Reactivate second user
        user = User.objects.get(username=_usernameLookup)
        user.is_active = True
        user.save()
        call_command("ldap_clean_users", superuser=False, verbosity=0)
        self.assertEqual(User.objects.get(username=_username).is_active, True)
        self.assertEqual(User.objects.get(username=_usernameLookup).is_active, False)
        call_command("ldap_clean_users", superuser=True, verbosity=0)
        self.assertEqual(User.objects.get(username=_username).is_active, False)

        """
        Test with staff user
        """
        # Reactivate first user and promote to staff
        user = User.objects.get(username=_username)
        user.is_active = True
        user.is_superuser = False
        user.is_staff = True
        user.save()
        # Reactivate second user
        user = User.objects.get(username=_usernameLookup)
        user.is_active = True
        user.save()
        call_command("ldap_clean_users", staff=False, verbosity=0)
        self.assertEqual(User.objects.get(username=_username).is_active, True)
        self.assertEqual(User.objects.get(username=_usernameLookup).is_active, False)
        call_command("ldap_clean_users", staff=True, verbosity=0)
        self.assertEqual(User.objects.get(username=_username).is_active, False)

    def testCleanUsersPurge(self):
        """
        ldap_clean_users management command test with purge argument
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            "nonldap{user}".format(user=settings.LDAP_AUTH_TEST_USER_USERNAME),
            "nonldap{mail}".format(mail=settings.LDAP_AUTH_TEST_USER_EMAIL),
            settings.LDAP_AUTH_TEST_USER_PASSWORD)
        user.save()
        user_count_1 = User.objects.count()
        call_command("ldap_clean_users", verbosity=0, purge=True)
        user_count_2 = User.objects.count()
        self.assertGreater(user_count_1, user_count_2)

    def testCleanUsersCommandOutput(self):
        # Test without purge
        out = StringIO()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            "nonldap{user}".format(user=settings.LDAP_AUTH_TEST_USER_USERNAME),
            "nonldap{mail}".format(mail=settings.LDAP_AUTH_TEST_USER_EMAIL),
            settings.LDAP_AUTH_TEST_USER_PASSWORD)
        user.save()
        call_command("ldap_clean_users", stdout=out, verbosity=1)
        rows = out.getvalue().split("\n")[:-1]
        self.assertEqual(len(rows), 1)
        for row in rows:
            self.assertRegex(row, r'^Deactivated ')
        # Reset for next test
        user.delete()
        out.truncate(0)
        out.seek(0)
        # Test with purge
        user = User.objects.create_user(
            "nonldap{user}".format(user=settings.LDAP_AUTH_TEST_USER_USERNAME),
            "nonldap{mail}".format(mail=settings.LDAP_AUTH_TEST_USER_EMAIL),
            settings.LDAP_AUTH_TEST_USER_PASSWORD)
        user.save()
        call_command("ldap_clean_users", stdout=out, verbosity=1, purge=True)
        rows = out.getvalue().split("\n")[:-1]
        self.assertEqual(len(rows), 1)
        for row in rows:
            self.assertRegex(row, r'^Purged ')

    def testReCleanUsersDoesntRecreateUsers(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            "nonldap{user}".format(user=settings.LDAP_AUTH_TEST_USER_USERNAME),
            "nonldap{mail}".format(mail=settings.LDAP_AUTH_TEST_USER_EMAIL),
            settings.LDAP_AUTH_TEST_USER_PASSWORD)
        user.save()
        call_command("ldap_clean_users", verbosity=0, purge=True)
        user_count_1 = User.objects.count()
        call_command("ldap_clean_users", verbosity=0, purge=True)
        user_count_2 = User.objects.count()
        self.assertEqual(user_count_1, user_count_2)
