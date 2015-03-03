"""
Low-level LDAP hooks.
"""

import ldap3

from contextlib import contextmanager

from django.contrib.auth import get_user_model

from django_python3_ldap.conf import settings
from django_python3_ldap.utils import clean_ldap_name, resolve_user_identifier


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
        user_data = settings.LDAP_AUTH_CLEAN_USER_DATA(user_fields)
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
        # All done!
        return user

    def iter_users(self):
        """
        Returns an iterator of Django users that correspond to
        users in the LDAP database.
        """
        paged_entries = self._connection.extend.standard.paged_search(
            search_base = settings.LDAP_AUTH_SEARCH_BASE,
            search_filter = "(objectClass={object_class})".format(
                object_class = clean_ldap_name(settings.LDAP_AUTH_OBJECT_CLASS),
            ),
            search_scope = ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
            attributes = list(settings.LDAP_AUTH_USER_FIELDS.values()),
            paged_size = 30,
        )
        return (
            self._get_or_create_user(entry)
            for entry
            in paged_entries
        )

    def get_user(self, *args, **kwargs):
        """
        Returns the user with the given identifier.

        The user identifier should either be keyword arguments,
        or positional arguments that match the fields in
        settings.LDAP_AUTH_USER_LOOKUP_FIELDS.

        For the default User model, this can therefor be in
        the form `get_user(username)` or `get_user(username=username)`.
        """
        # Parse the user lookup.
        user_identifier = resolve_user_identifier(settings.LDAP_AUTH_USER_LOOKUP_FIELDS, True, args, kwargs)
        # Search the LDAP database.
        search_filter = "(&(objectClass={object_class}){user_identifier})".format(
            object_class = clean_ldap_name(settings.LDAP_AUTH_OBJECT_CLASS),
            user_identifier = "".join(
                "({attribute_name}={field_value})".format(
                    attribute_name = clean_ldap_name(settings.LDAP_AUTH_USER_FIELDS[field_name]),
                    field_value = clean_ldap_name(field_value),
                )
                for field_name, field_value
                in user_identifier.items()
            ),
        )
        if self._connection.search(
            search_base = settings.LDAP_AUTH_SEARCH_BASE,
            search_filter = search_filter,
            search_scope = ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
            attributes = list(settings.LDAP_AUTH_USER_FIELDS.values()),
            size_limit = 1,
        ):
            return self._get_or_create_user(self._connection.response[0])
        return None


@contextmanager
def connection(*args, **kwargs):
    """
    Creates and returns a connection to the LDAP server.

    If a user identifier is given, it should either be
    keyword arguments, or positional arguments that match the fields in
    settings.LDAP_AUTH_USER_LOOKUP_FIELDS.

    The final positional argument, or the keyword argument `password`, will
    be taken as the user's password.
    """
    # Parse the user lookup.
    user_identifier = resolve_user_identifier(settings.LDAP_AUTH_USER_LOOKUP_FIELDS + ("password",), False, args, kwargs)
    # Format the DN for the username.
    if user_identifier:
        password = user_identifier.pop("password")
        username_dn = "{user_identifier},{search_base}".format(
            user_identifier = ",".join(
                "{attribute_name}={field_value}".format(
                    attribute_name = clean_ldap_name(settings.LDAP_AUTH_USER_FIELDS[field_name]),
                    field_value = clean_ldap_name(field_value),
                )
                for field_name, field_value
                in user_identifier.items()
            ),
            search_base = settings.LDAP_AUTH_SEARCH_BASE,
        )
    else:
        password = None
        username_dn = None
    # Make the connection.
    with ldap3.Connection(ldap3.Server(settings.LDAP_AUTH_URL), user=username_dn, password=password, auto_bind=ldap3.AUTO_BIND_NONE) as c:

        if settings.LDAP_AUTH_USE_TLS:
            c.start_tls()

        # Attempt authentication, if required.
        if user_identifier and not c.bind():
            yield None
        else:
            # We authenticated, so let's return the connection.
            auth_connection = Connection(c)
            yield auth_connection


def authenticate(*args, **kwargs):
    """
    Authenticates with the LDAP server, and returns
    the corresponding Django user instance.

    The user identifier should either be
    keyword arguments, or positional arguments that match the fields in
    settings.LDAP_AUTH_USER_LOOKUP_FIELDS.

    The final positional argument, or the keyword argument `password`, will
    be taken as the user's password.
    """
    user_identifier = resolve_user_identifier(settings.LDAP_AUTH_USER_LOOKUP_FIELDS + ("password",), True, args, kwargs)
    user_identifier.pop("password")
    with connection(*args, **kwargs) as c:
        if c is None:
            return None
        return c.get_user(**user_identifier)
