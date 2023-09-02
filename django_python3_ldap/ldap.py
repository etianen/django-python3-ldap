"""
Low-level LDAP hooks.
"""

import ldap3
from ldap3.core.exceptions import LDAPException
import logging
from inspect import getfullargspec
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

        attributes = user_data.get("attributes")
        if attributes is None:
            logger.warning("LDAP user attributes empty")
            return None

        User = get_user_model()

        # Create the user data.
        user_fields = {
            field_name: (
                attributes[attribute_name][0]
                if isinstance(attributes[attribute_name], (list, tuple)) else
                attributes[attribute_name]
            )
            for field_name, attribute_name
            in settings.LDAP_AUTH_USER_FIELDS.items()
            if attribute_name in attributes
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
            defaults=user_fields,
            **user_lookup
        )
        # If the user was created, set them an unusable password.
        if created:
            user.set_unusable_password()
            user.save()
        # Update relations
        sync_user_relations_func = import_func(settings.LDAP_AUTH_SYNC_USER_RELATIONS)
        sync_user_relations_arginfo = getfullargspec(sync_user_relations_func)
        args = {}  # additional keyword arguments
        for argname in sync_user_relations_arginfo.kwonlyargs:
            if argname == "connection":
                args["connection"] = self._connection
            elif argname == "dn":
                args["dn"] = user_data.get("dn")
            else:
                raise TypeError(f"Unknown kw argument {argname} in signature for LDAP_AUTH_SYNC_USER_RELATIONS")
        # call sync_user_relations_func() with original args plus supported named extras
        sync_user_relations_func(user, attributes, **args)
        # All done!
        logger.info("LDAP user lookup succeeded")
        return user

    def iter_users(self):
        """
        Returns an iterator of Django users that correspond to
        users in the LDAP database.
        """
        paged_entries = self._connection.extend.standard.paged_search(
            search_base=settings.LDAP_AUTH_SEARCH_BASE,
            search_filter=format_search_filter({}),
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
            get_operational_attributes=True,
            paged_size=30,
        )
        return filter(None, (
            self._get_or_create_user(entry)
            for entry
            in paged_entries
            if entry["type"] == "searchResEntry"
        ))

    def get_user(self, **kwargs):
        """
        Returns the user with the given identifier.

        The user identifier should be keyword arguments matching the fields
        in settings.LDAP_AUTH_USER_LOOKUP_FIELDS.
        """
        # Search the LDAP database.
        if self.has_user(**kwargs):
            return self._get_or_create_user(self._connection.response[0])
        logger.warning("LDAP user lookup failed")
        return None

    def has_user(self, **kwargs):
        """
        Returns True if the user with the given identifier exists.

        The user identifier should be keyword arguments matching the fields
        in settings.LDAP_AUTH_USER_LOOKUP_FIELDS.
        """
        # Search the LDAP database.
        self._connection.search(
            search_base=settings.LDAP_AUTH_SEARCH_BASE,
            search_filter=format_search_filter(kwargs),
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
            get_operational_attributes=True,
            size_limit=1,
        )
        return bool(len(self._connection.response) > 0 and self._connection.response[0].get("attributes"))


@contextmanager
def connection(**kwargs):
    """
    Creates and returns a connection to the LDAP server.

    The user identifier, if given, should be keyword arguments matching the fields
    in settings.LDAP_AUTH_USER_LOOKUP_FIELDS, plus a `password` argument.
    """
    # Format the DN for the username.
    format_username = import_func(settings.LDAP_AUTH_FORMAT_USERNAME)
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
        username = format_username(kwargs)
    # Build server pool
    server_pool = ldap3.ServerPool(None, ldap3.RANDOM, active=True, exhaust=5)
    auth_url = settings.LDAP_AUTH_URL
    if not isinstance(auth_url, list):
        auth_url = [auth_url]
    for u in auth_url:
        # Include SSL / TLS, if requested.
        server_args = {
            "allowed_referral_hosts": [("*", True)],
            "get_info": ldap3.NONE,
            "connect_timeout": settings.LDAP_AUTH_CONNECT_TIMEOUT,
        }
        if settings.LDAP_AUTH_USE_TLS:
            server_args["tls"] = ldap3.Tls(
                ciphers="ALL",
                version=settings.LDAP_AUTH_TLS_VERSION,
            )
        server_pool.add(
            ldap3.Server(
                u,
                **server_args,
            )
        )
    # Connect.
    try:
        connection_args = {
            "user": username,
            "password": password,
            "auto_bind": False,
            "raise_exceptions": True,
            "receive_timeout": settings.LDAP_AUTH_RECEIVE_TIMEOUT,
        }
        c = ldap3.Connection(
            server_pool,
            **connection_args,
        )
    except LDAPException as ex:
        logger.warning("LDAP connect failed: {ex}".format(ex=ex))
        yield None
        return
    # Configure.
    try:
        # Start TLS, if requested.
        if settings.LDAP_AUTH_USE_TLS:
            c.start_tls(read_server_info=False)
        # Perform initial authentication bind.
        c.bind(read_server_info=True)
        User = get_user_model()
        # If the settings specify an alternative username and password for querying, rebind as that.
        settings_username = (
            format_username(
                {User.USERNAME_FIELD: settings.LDAP_AUTH_CONNECTION_USERNAME}
            )
            if settings.LDAP_AUTH_CONNECTION_USERNAME
            else None
        )
        settings_password = settings.LDAP_AUTH_CONNECTION_PASSWORD
        if (settings_username or settings_password) and (
            settings_username != username or settings_password != password
        ):
            c.rebind(
                user=settings_username,
                password=settings_password,
            )
        # Return the connection.
        logger.info("LDAP connect succeeded")
        yield Connection(c)
    except LDAPException as ex:
        logger.warning("LDAP bind failed: {ex}".format(ex=ex))
        yield None
    finally:
        c.unbind()


def authenticate(*args, **kwargs):
    """
    Authenticates with the LDAP server, and returns
    the corresponding Django user instance.

    The user identifier should be keyword arguments matching the fields
    in settings.LDAP_AUTH_USER_LOOKUP_FIELDS, plus a `password` argument.
    """
    password = kwargs.pop("password", None)
    auth_user_lookup_fields = frozenset(settings.LDAP_AUTH_USER_LOOKUP_FIELDS)
    ldap_kwargs = {
        key: value for (key, value) in kwargs.items()
        if key in auth_user_lookup_fields
    }

    # Check that this is valid login data.
    if not password or frozenset(ldap_kwargs.keys()) != auth_user_lookup_fields:
        return None

    # Connect to LDAP.
    with connection(password=password, **ldap_kwargs) as c:
        if c is None:
            return None
        return c.get_user(**ldap_kwargs)
