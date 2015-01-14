"""
Some useful LDAP utilities.
"""

import re

from django.contrib.auth.hashers import make_password
from django.utils.encoding import force_text


def clean_ldap_name(name):
    """
    Transforms the given name into a form that
    won't interfere with LDAP queries.
    """
    # HACK: There is probably an official way to escape LDAP
    # values, but I can't find the documentation anywhere!
    # This just removes bad characters entirely, which will
    # work for most cases, but isn't exactly ideal! :O
    return re.sub("[^a-zA-Z0-9_\-]", "", force_text(name))


def clean_user_data(user_data):
    """
    Transforms the user data loaded from
    LDAP into a form suitable for creating a user.
    """
    # Create an unusable password for the user.
    user_data["password"] = make_password(None)
    return user_data


def resolve_user_identifier(lookup_fields, required, args, kwargs):
    """
    Resolves a user identifier from the given args
    and kwargs.

    If a user identifier is given, it should either be
    keyword arguments, or positional arguments that match the fields in
    settings.LDAP_AUTH_USER_LOOKUP_FIELDS.
    """
    # Raises a type error if the args are incorrect.
    def raise_error():
        raise TypeError("Expected arguments: {lookup_fields}".format(
            lookup_fields = ", ".join(map(force_text, lookup_fields)),
        ))
    # Cannot use both args and kwargs.
    if args and kwargs:
        raise TypeError("Cannot use both args and kwargs to identify a user")
    # Parse args.
    if args:
        if len(lookup_fields) != len(args):
            raise_error()
        return dict(zip(lookup_fields, args))
    # Parse kwargs.
    if kwargs:
        if frozenset(lookup_fields) != frozenset(kwargs.keys()):
            raise_error()
        return kwargs.copy()
    # No user identifier.
    if required:
        raise_error()
    # All done!
    return {}
