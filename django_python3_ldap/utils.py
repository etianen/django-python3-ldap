"""
Some useful LDAP utilities.
"""

import re
import binascii
from django.utils.encoding import force_text
from django.utils.module_loading import import_string
from django.utils import six

from django_python3_ldap.conf import settings


def import_func(func):
    if callable(func):
        return func
    elif isinstance(func, six.string_types):
        return import_string(func)
    raise AttributeError("Expected a function {0!r}".format(func))


def clean_ldap_name(name):
    """
    Transforms the given name into a form that
    won't interfere with LDAP queries.
    """
    return re.sub(
        r'[^a-zA-Z0-9 _\-.@:*]',
        lambda c: "\\" + force_text(binascii.hexlify(c.group(0).encode("latin-1", errors="ignore"))).upper(),
        force_text(name),
    )


def convert_model_fields_to_ldap_fields(model_fields):
    """
    Converts a set of model fields into a set of corresponding
    LDAP fields.
    """
    return {
        settings.LDAP_AUTH_USER_FIELDS[field_name]: field_value
        for field_name, field_value
        in model_fields.items()
    }


def format_search_filter(model_fields):
    """
    Creates an LDAP search filter for the given set of model
    fields.
    """
    ldap_fields = convert_model_fields_to_ldap_fields(model_fields)
    ldap_fields["objectClass"] = settings.LDAP_AUTH_OBJECT_CLASS
    search_filters = import_func(settings.LDAP_AUTH_FORMAT_SEARCH_FILTERS)(ldap_fields)
    return "(&{})".format("".join(search_filters))


def clean_user_data(model_fields):
    """
    Transforms the user data loaded from
    LDAP into a form suitable for creating a user.
    """
    return model_fields


def format_username_openldap(model_fields):
    """
    Formats a user identifier into a username suitable for
    binding to an OpenLDAP server.
    """
    return "{user_identifier},{search_base}".format(
        user_identifier=",".join(
            "{attribute_name}={field_value}".format(
                attribute_name=clean_ldap_name(field_name),
                field_value=clean_ldap_name(field_value),
            )
            for field_name, field_value
            in convert_model_fields_to_ldap_fields(model_fields).items()
        ),
        search_base=settings.LDAP_AUTH_SEARCH_BASE,
    )


def format_username_active_directory(model_fields):
    """
    Formats a user identifier into a username suitable for
    binding to an Active Directory server.
    """
    username = model_fields["username"]
    if settings.LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN:
        username = "{domain}\\{username}".format(
            domain=settings.LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN,
            username=username,
        )
    return username


def format_username_active_directory_principal(model_fields):
    """
    Formats a user identifier into a username suitable for
    binding to an Active Directory server.
    """
    username = model_fields["username"]
    if settings.LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN:
        username = "{username}@{domain}".format(
            username=username,
            domain=settings.LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN,
        )
    return username


def sync_user_relations(user, ldap_attributes):
    # do nothing by default
    pass


def format_search_filters(ldap_fields):
    return [
        "({attribute_name}={field_value})".format(
            attribute_name=clean_ldap_name(field_name),
            field_value=clean_ldap_name(field_value),
        )
        for field_name, field_value
        in ldap_fields.items()
    ]
