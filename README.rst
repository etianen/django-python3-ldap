django-python3-ldap
===================

**django-python3-ldap** provides a Django LDAP user authentication backend for Python 2 and 3.


Features
--------

- Authenticate users with an LDAP server.
- Sync LDAP users with a local Django database.
- Supports custom Django user models.
- Works in Python 2 and 3!


Installation
------------

1. Install using ``pip install django-python3-ldap``.
2. Add ``'django_python3_ldap'`` to your ``INSTALLED_APPS`` setting.
3. Set your ``AUTHENTICATION_BACKENDS`` setting to ``("django_python3_ldap.auth.LDAPBackend",)``
4. Configure the settings for your LDAP server (see Available settings, below).
5. Optionally, run ``./manage.py ldap_sync_users`` to perform an initial sync of LDAP users.
6. Optionally, run ``./manage.py ldap_promote <username>`` to grant superuser admin access to a given user.


Available settings
------------------

**Note**: The settings below show their default values. You only need to add settings to your ``settings.py`` file that you intend to override.


.. code:: python

    # The URL of the LDAP server.
    LDAP_AUTH_URL = "ldap://localhost:389"

    # Initiate TLS on connection.
    LDAP_AUTH_USE_TLS = False

    # The LDAP search base for looking up users.
    LDAP_AUTH_SEARCH_BASE = "ou=people,dc=example,dc=com"

    # The LDAP class that represents a user.
    LDAP_AUTH_OBJECT_CLASS = "inetOrgPerson"

    # User model fields mapped to the LDAP
    # attributes that represent them.
    LDAP_AUTH_USER_FIELDS = {
        "username": "uid",
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
    }

    # A tuple of django model fields used to uniquely identify a user.
    LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)

    # Path to a callable that takes a dict of {model_field_name: value},
    # returning a dict of clean model data.
    # Use this to customize how data loaded from LDAP is saved to the User model.
    LDAP_AUTH_CLEAN_USER_DATA = "django_python3_ldap.utils.clean_user_data"

    # Path to a callable that takes a user model and a dict of {ldap_field_name: [value]},
    # and saves any additional user relationships based on the LDAP data.
    # Use this to customize how data loaded from LDAP is saved to User model relations.
    # For customizing non-related User model fields, use LDAP_AUTH_CLEAN_USER_DATA.
    LDAP_AUTH_SYNC_USER_RELATIONS = "django_python3_ldap.utils.sync_user_relations"

    # Path to a callable that takes a dict of {ldap_field_name: value},
    # returning a list of [ldap_search_filter]. The search filters will then be AND'd
    # together when creating the final search filter.
    LDAP_AUTH_FORMAT_SEARCH_FILTERS = "django_python3_ldap.utils.format_search_filters"

    # Path to a callable that takes a dict of {model_field_name: value}, and returns
    # a string of the username to bind to the LDAP server.
    # Use this to support different types of LDAP server.
    LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_openldap"

    # Sets the login domain for Active Directory users.
    LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = None

    # The LDAP username and password of a user for querying the LDAP database for user
    # details. If None, then the authenticated user will be used for querying, and
    # the `ldap_sync_users` command will perform an anonymous query.
    LDAP_AUTH_CONNECTION_USERNAME = None
    LDAP_AUTH_CONNECTION_PASSWORD = None


Microsoft Active Directory support
----------------------------------

django-python3-ldap is configured by default to support login via OpenLDAP. To connect to
a Microsoft Active Directory, you need to modify your settings file.

For simple usernames (e.g. "username"):

.. code:: python

    LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_active_directory"

For down-level login name formats (e.g. "DOMAIN\\username"):

.. code:: python

    LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_active_directory"
    LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = "DOMAIN"

For user-principal-name formats (e.g. "user@domain.com"):

.. code:: python

    LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_active_directory_principal"
    LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = "domain.com"


Can't get authentication to work?
---------------------------------

LDAP is a very complicated protocol. Enable logging (see below), and see what error messages the LDAP connection is throwing.


Logging
-------

Print information about failed logins to your console by adding the following to your ``settings.py`` file.

.. code:: python

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "django_python3_ldap": {
                "handlers": ["console"],
                "level": "INFO",
            },
        },
    }


Custom user filters
-------------------

By default, any users within ``LDAP_AUTH_SEARCH_BASE`` and of the correct ``LDAP_AUTH_OBJECT_CLASS``
will be considered a valid user. You can apply further filtering by setting a custom ``LDAP_AUTH_FORMAT_SEARCH_FILTERS``
callable.

.. code:: python

    # settings.py
    LDAP_AUTH_FORMAT_SEARCH_FILTERS = "path.to.your.custom_format_search_filters"

    # pay/to/your.py
    from django_python3_ldap.utils import format_search_filters

    def custom_format_search_filters(ldap_fields):
        # Add in simple filters.
        ldap_fields["memberOf"] = "foo"
        # Call the base format callable.
        search_filters = format_search_filters(ldap_fields)
        # Advanced: apply custom LDAP filter logic.
        search_filters.append("(|(memberOf=groupA)(memberOf=GroupB))")
        # All done!
        return search_filters

The returned list of search filters will be AND'd together to make the final search filter.


How it works
------------

When a user attempts to authenticate, a connection is made to the LDAP
server, and the application attempts to bind using the provided username and password.

If the bind attempt is successful, the user details are loaded from the LDAP server
and saved in a local Django ``User`` model. The local model is only created once,
and the details will be kept updated with the LDAP record details on every login.

To perform a full sync of all LDAP users to the local database, run ``./manage.py ldap_sync_users``.
This is not required, as the authentication backend will create users on demand. Syncing users has
the advantage of allowing you to assign permissions and groups to the existing users using the Django
admin interface.

Running ``ldap_sync_users`` as a background cron task is another optional way to
keep all users in sync on a regular basis.

Simple Authentication Example
-----------------------------

This example assumes your LDAP server accepts anonymous binding. You will need to change the values of ``LDAP_AUTH_URL`` and ``LDAP_AUTH_SEARCH_BASE`` to match your server setup.

If you need a test server, `freeIPA.org <https://www.freeipa.org/page/Demo>`_ has good options.  The example here will use their demo server.  Though you can install a local server, or use an existing one if you can find the settings for it. 

1. Install **django** and **django-python3-ldap** as instructed above
2. Edit ``settings.py`` to include the following (Adjusting to your LDAP settings):

.. code:: python

    # settings.py
    INSTALLED_APPS = [
        ... # Your existing installed apps
        'django_python3_ldap',
    ]

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'django_python3_ldap.auth.LDAPBackend',
    ]

    LDAP_AUTH_URL = 'ldap://ipa.demo1.freeipa.org:389'
    LDAP_AUTH_SEARCH_BASE = 'cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org'

3. Sync the LDAP users to the local user model ``./manage.py ldap_sync_users`` *(You should see a list of 3 users show as synced)*
4. Create a local superuser ``python manage.py createsuperuser`` following the prompts
5. Login as that user `example.com/admin <http://example.com/admin>`_
6. Open `example.com/admin/user <http://example.com/admin/user>`_ to view list of synced accounts
7. Open detail for a user you know the LDAP credentials of and set Staff status and/or Superuser status for that user.
8. Logout
9. Login as the LDAP user you just gave permissions to, using the LDAP credentials
10. If you gave superuser permission, you should be able to see the list of users `example.com/admin/user <http://example.com/admin/user>`_

``'django_python3_ldap.auth.LDAPBackend'`` creates a connection to the LDAP database and can authenticate against it. But all of them are set with no permissions initially. So while you can use them with custom models, it's necessary to add ``'django.contrib.auth.backends.ModelBackend'`` to make those users accessible from django backend admin so you can easily manage permissions.

Having more than one ``AUTHENTICATION_BACKENDS`` causes django to attempt authentication against them in order listed so that if the ``ModelBackend`` auth fails, as any user not created in the app locally would, it will fall through to attempt against LDAP.

**Note:** Any time a user is successfully authenticated through the LDAP backend when there wasn't already a user record in the user model, the user will be created in the user model, but will not have any permissions. So if there is an attempt for a user to login through the Admin interface before that user has a record, a record will be created, but to the user it will appear to be a failed login with the message "Please enter the correct username and password for a staff account." . A superuser will have to give the user at least Staff permission for the user to successfully login to the Admin interface.

Tips
----

- If a user last authenticated against LDAP, the local password in the admin will show "No password set".  If a user with admin rights through ModelBackend sets a password for a user that was previously authenticating against LDAP, that new password will work for the user. But if the user successfully authenticates against the LDAP server (assuming the password is not the same as the local one, causing it to succeed locally), the local one will be removed and the user record will once again show "No password set".

- The ``ModelBackend`` is not required for **django-python3-ldap** to be used. Users will still sync to the user module in django. But the admin interface will not be available to manage users and there will need to be another mechanism provided.

Support and announcements
-------------------------

Downloads and bug tracking can be found at the `main project
website <http://github.com/etianen/django-python3-ldap>`_.


More information
----------------

The django-python3-ldap project was developed by Dave Hall. You can get the code
from the `django-python3-ldap project site <http://github.com/etianen/django-python3-ldap>`_.

Dave Hall is a freelance web developer, based in Cambridge, UK. You can usually
find him on the Internet in a number of different places:

-  `Website <http://www.etianen.com/>`_
-  `Twitter <http://twitter.com/etianen>`_
-  `Google Profile <http://www.google.com/profiles/david.etianen>`_
