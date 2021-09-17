# Reusable components

- The django apps [admin.core](../src/os2datascanner/projects/admin/core), [admin.organisation](../src/os2datascanner/projects/admin/organizations) and [admin.import_services](../src/os2datascanner/projects/admin/import_services) can be reused to support LDAP synchronization through Keycloak. They support import of both Org. Units and Groups.  
- [pika.py](../src/os2datascanner/engine2/pipeline/utilities/pika.py) manages a Pika connection and can with some modification be used in other python projects using Pika and RabbitMQ.
- [backoff.py](../src/os2datascanner/engine2/utilities/backoff.py) can be used whenever a backoff algorithm is needed.
- [aescipher.py](../src/os2datascanner/projects/admin/adminapp/aescipher.py) can be reused to AES encrypt and decrypt text.