Using the system
****************

Creating Django superusers
==========================

The Django apps use Django's normal access control mechanisms. To create a user
with full privileges, use the ``createsuperuser`` command for each app:

* For the :ref:`"raw" install<raw-install>`:

  - ``bin/manage-admin createsuperuser``
  - ``bin/manage-report createsuperuser``

* For the :ref:`docker-based install<docker-install>` (using ``docker-compose``):

  - :code:`<docker-compose exec admin-application> python manage.py createsuperuser`
  - :code:`<docker-compose exec report-application> python manage.py createsuperuser`

The ``createsuperuser`` command will prompt for a username, an email address,
and a password for the new accounts.

(Once a superuser account has been created, it can be used in the Django
administration interface to create accounts with more granular permissions.)


Using the *administration interface*
====================================

.. include:: interfaces-admin.rst

