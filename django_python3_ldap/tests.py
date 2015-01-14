from unittest import skipUnless

from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.core.management import call_command

from django_python3_ldap.conf import settings


@skipUnless(settings.LDAP_TEST_USER_USERNAME, "No settings.LDAP_TEST_USER_USERNAME supplied.")
@skipUnless(settings.LDAP_TEST_USER_PASSWORD, "No settings.LDAP_TEST_USER_PASSWORD supplied.")
@skipUnless(django_settings.AUTH_USER_MODEL == "auth.User", "Cannot test using a custom user model.")
class TestLdap(TestCase):

    def setUp(self):
        super().setUp()
        User.objects.all().delete()

    # Authentication tests.

    def testAuthenticateUserSuccess(self):
        user = authenticate(
            username = settings.LDAP_TEST_USER_USERNAME,
            password = settings.LDAP_TEST_USER_PASSWORD,
        )
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, settings.LDAP_TEST_USER_USERNAME)
        
    def testAuthenticateUserBadUsername(self):
        user = authenticate(
            username = "bad" + settings.LDAP_TEST_USER_USERNAME,
            password = settings.LDAP_TEST_USER_PASSWORD,
        )
        self.assertEqual(user, None)

    def testAuthenticateUserBadPassword(self):
        user = authenticate(
            username = settings.LDAP_TEST_USER_USERNAME,
            password = "bad" + settings.LDAP_TEST_USER_PASSWORD,
        )
        self.assertEqual(user, None)

    def testRepeatedUserAuthentication(self):
        user_1 = authenticate(
            username = settings.LDAP_TEST_USER_USERNAME,
            password = settings.LDAP_TEST_USER_PASSWORD,
        )
        user_2 = authenticate(
            username = settings.LDAP_TEST_USER_USERNAME,
            password = settings.LDAP_TEST_USER_PASSWORD,
        )
        # Ensure that the user isn't recreated on second access.
        self.assertEqual(user_1.pk, user_2.pk)

    # User syncronisation.

    def testSyncUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        self.assertGreater(User.objects.count(), 0)

    def testReSyncUsers(self):
        call_command("ldap_sync_users", verbosity=0)
        user_count_1 = User.objects.count()
        call_command("ldap_sync_users", verbosity=0)
        user_count_2 = User.objects.count()
        self.assertEqual(user_count_1, user_count_2)
