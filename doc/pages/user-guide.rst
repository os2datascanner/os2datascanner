.. :index:

Using OS2datascanner
********************

Creating Django superusers
==========================

The Django apps use Django's normal access control mechanisms. To create a user
with full privileges, use the ``createsuperuser`` command for each app:

* For the :ref:`"raw" install<raw-install>`:

  - ``bin/manage-admin createsuperuser``
  - ``bin/manage-report createsuperuser``

* For the :ref:`docker-based install<docker-install>` (using ``docker-compose``):

  - :code:`<docker-compose exec admin> python manage.py createsuperuser`
  - :code:`<docker-compose exec report> python manage.py createsuperuser`

The ``createsuperuser`` command will prompt for a username, an email address,
and a password for the new accounts.

(Once a superuser account has been created, it can be used in the Django
administration interface to create accounts with more granular permissions.)


.. include:: interfaces-admin.rst
.. include:: interfaces-report.rst
.. include:: rules.rst
