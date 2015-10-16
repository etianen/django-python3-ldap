django-python3-ldap
===================

**django-python3-ldap** provides a Django LDAP user authentication backend for Python 3.


Features
--------

- Authenticate users with an LDAP server.
- Sync LDAP users with a local Django database.
- Supports custom Django user models.
- Works in Python 3!


Installation
------------

1. Install using ``pip install django-python3-ldap``.
2. Add ``'django_python3_ldap'`` to your ``INSTALLED_APPS`` setting.
3. Set your ``AUTHENTICATION_BACKENDS`` setting to ``("django_python3_ldap.auth.LDAPBackend",)``
4. Configure the settings for your LDAP server (see Available settings, below).
5. Optionally, run ``./manage.py ldap_sync_users`` to perform an initial sync of LDAP users.


Available settings
------------------

::

    # The URL of the LDAP server.
    LDAP_AUTH_URL = "ldap://localhost:389"

    # Initiate TLS on connection.
    LDAP_AUTH_USE_TLS = False

    # The LDAP search base for looking up users.
    LDAP_AUTH_SEARCH_BASE = "ou=people,dc=example,dc=com"

    # The LDAP class that represents a user.
    LDAP_AUTH_OBJECT_CLASS = "inetOrgPerson"

    # Extra LDAP search filter for matching users.
    LDAP_AUTH_SEARCH_EXTRA_FILTER = ""

    # The LDAP Username and password of a user so ldap_sync_users can be run
    # Set to None if you allow anonymous queries
    LDAP_AUTH_CONNECTION_USERNAME = None
    LDAP_AUTH_CONNECTION_PASSWORD = None

    # User model fields mapped to the LDAP
    # attributes that represent them.
    LDAP_AUTH_USER_FIELDS = {
        "username": "uid",
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
    }

    # A tuple of fields used to uniquely identify a user.
    LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)

    # Dotted path to callable that transforms the user data loaded from
    # LDAP into a form suitable for creating a user.
    # Override this to set custom field formatting for your
    # user model.
    LDAP_AUTH_CLEAN_USER_DATA = "django_python3_ldap.utils.clean_user_data"

    # Dotted path to callable that can be used to store additional information
    # from LDAP data to user-related models. For example,
    # it can be used to synchronize LDAP-groups with Django groups.
    # Takes two parameters: user object and dictionary of ldap data
    LDAP_AUTH_SYNC_USER_RELATIONS = "django_python3_ldap.utils.sync_user_relations"


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
