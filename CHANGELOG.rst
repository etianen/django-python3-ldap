django-python3-ldap changelog
=============================

Development
-----------

- Added `django_python3_ldap.utils.format_username_active_directory_principal` option for formatting user-principal-name (e.g. "user@domain.com") Active Directory usernames.


0.9.14
------

- Django 1.11 compatibility (@aritas1).


0.9.13
------

- Fixed issue with LDAP servers returning attributes that are not a list (@etianen).


0.9.12
------

- Update for compatibility with ldap3 2.x release (@etianen).


0.9.11
------

- Added support for LDAP referrals (@etianen).
- Fixed issue with missing LDAP attributes (@smills2929).
- Tweaks and bugfixes (@smills2929).


0.9.10
------

- Django 1.10 compatibility (@etianen, @frennkie).
- Added operational LDAP attributes to ``iter_users`` (@frennkie).
- Dropped Django 1.7 compatibility (@etianen).
- Dropped Python 3.2 and 3.3 compatibility (@etianen).


0.9.9
-----

- Fixing anonymous bind in some LDAP servers (@etianen).


0.9.8
-----

- Fixing security vulnerability allowing users to authenticate with a valid username but with an empty password if anonymous authentication is allowed on the LDAP server (Petros Moisiadis).
- Fixing sync_users command for Microsoft Active Directory (@jjagielka).


0.9.7
-----

- Ability to configure extra filters for user lookup using LDAP_AUTH_SEARCH_FILTERS (@etianen, @Ernest0x).
- Support for Active Directory LDAP servers (@etianen, @brandonusher).
- Python 2.7 compatibility (@NotSqrt).
- Ability to configure relations on loaded user models using LDAP_AUTH_SYNC_USER_RELATIONS (@mnach).
- Switched to specifying paths to functions using dotted string paths in settings (@mnach).


0.9.6
-----

- Added settings option for a username and password to be specified incase anonymous user queries are not allowed (@brandonusher).


0.9.5
-----

- Fixing security vulnerability where username and password could be transmitted in plain text before starting TLS (reported by Weitzhofer Bernhard).


0.9.4
-----

- Fixing broken ldap3 dependency (@levisaya).
- Honoring LDAP_AUTH_CLEAN_USER_DATA setting (@etianen, @akaariai).


0.9.3
-----

- Fixing broken python3-ldap dependency (@ricard33).


0.9.2
-----

- Added setting for initiating TLS on connection (@saraheiting).


0.9.1
-----

- Adding ldap_promote management command.


0.9.0
-----

- First production release.
