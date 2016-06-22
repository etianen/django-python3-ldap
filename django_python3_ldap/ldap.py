"""
Low-level LDAP hooks.
"""

import ldap3
import logging

from contextlib import contextmanager

from django.contrib.auth import get_user_model

from django_python3_ldap.conf import settings
from django_python3_ldap.utils import import_func, format_search_filter


logger = logging.getLogger(__name__)


class Connection(object):

    """
    A connection to an LDAP server.
    """

    def __init__(self, connection):
        """
        Creates the LDAP connection.

        No need to call this manually, the `connection()` context
        manager handles initialization.
        """
        self._connection = connection

    def _get_or_create_user(self, user_data):
        """
        Returns a Django user for the given LDAP user data.

        If the user does not exist, then it will be created.
        """
        User = get_user_model()
        attributes = user_data["attributes"]
        # Create the user data.
        user_fields = {
            field_name: attributes.get(attribute_name, ("",))[0]
            for field_name, attribute_name
            in settings.LDAP_AUTH_USER_FIELDS.items()
        }
        user_fields = import_func(settings.LDAP_AUTH_CLEAN_USER_DATA)(user_fields)
        # Create the user lookup.
        user_lookup = {
            field_name: user_fields.pop(field_name, "")
            for field_name
            in settings.LDAP_AUTH_USER_LOOKUP_FIELDS
        }
        # Update or create the user.
        user, created = User.objects.update_or_create(
            defaults = user_fields,
            **user_lookup
        )
        # Update relations
        import_func(settings.LDAP_AUTH_SYNC_USER_RELATIONS)(user, attributes)
        # All done!
        return user

    def iter_users(self):
        """
        Returns an iterator of Django users that correspond to
        users in the LDAP database.
        """
        paged_entries = self._connection.extend.standard.paged_search(
            search_base = settings.LDAP_AUTH_SEARCH_BASE,
            search_filter = format_search_filter({}),
            search_scope = ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
            attributes = ldap3.ALL_ATTRIBUTES,
            get_operational_attributes = True,
            paged_size = 30,
        )
        return (
            self._get_or_create_user(entry)
            for entry
            in paged_entries
            if entry["type"] == "searchResEntry"
        )

    def get_user(self, **kwargs):
        """
        Returns the user with the given identifier.

        The user identifier should be keyword arguments matching the fields
        in settings.LDAP_AUTH_USER_LOOKUP_FIELDS.
        """
        # Search the LDAP database.
        if self._connection.search(
            search_base = settings.LDAP_AUTH_SEARCH_BASE,
            search_filter = format_search_filter(kwargs),
            search_scope = ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
            attributes = ldap3.ALL_ATTRIBUTES,
            get_operational_attributes = True,
            size_limit = 1,
        ):
            return self._get_or_create_user(self._connection.response[0])
        return None


@contextmanager
def connection(**kwargs):
    """
    Creates and returns a connection to the LDAP server.

    The user identifier, if given, should be keyword arguments matching the fields
    in settings.LDAP_AUTH_USER_LOOKUP_FIELDS, plus a `password` argument.
    """
    # Format the DN for the username.
    kwargs = {
        key: value
        for key, value
        in kwargs.items()
        if value
    }
    username = None
    password = None
    if kwargs:
        password = kwargs.pop("password")
        username = import_func(settings.LDAP_AUTH_FORMAT_USERNAME)(kwargs)
    # Make the connection.
    if settings.LDAP_AUTH_USE_TLS:
        auto_bind = ldap3.AUTO_BIND_TLS_BEFORE_BIND
    else:
        auto_bind = ldap3.AUTO_BIND_NO_TLS
    try:
        with ldap3.Connection(ldap3.Server(settings.LDAP_AUTH_URL), user=username, password=password, auto_bind=auto_bind) as c:
            yield Connection(c)
    except ldap3.LDAPBindError as ex:
        logger.info("LDAP login failed: {ex}".format(ex=ex))
        yield None
    except ldap3.LDAPException as ex:
        logger.warn("LDAP connect failed: {ex}".format(ex=ex))
        yield None


def authenticate(**kwargs):
    """
    Authenticates with the LDAP server, and returns
    the corresponding Django user instance.

    The user identifier should be keyword arguments matching the fields
    in settings.LDAP_AUTH_USER_LOOKUP_FIELDS, plus a `password` argument.
    """
    password = kwargs.pop("password")
    # Check that this is valid login data.
    if not password or frozenset(kwargs.keys()) != frozenset(settings.LDAP_AUTH_USER_LOOKUP_FIELDS):
        return None
    # Connect to LDAP.
    with connection(password=password, **kwargs) as c:
        if c is None:
            return None
        return c.get_user(**kwargs)
