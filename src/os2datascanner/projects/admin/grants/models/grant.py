from django.db import models


class Grant(models.Model):
    """A Grant represents an entitlement to use an external API, issued to this
    OS2datascanner instance by an external gatekeeper.

    Grants exist to allow a separation between the roles of the organisational
    administrator, who can delegate functions to OS2datascanner, and the
    OS2datascanner administrator, who does not necessarily have that power."""

    organization = models.ForeignKey(
            'organizations.Organization',
            related_name="grants",
            on_delete=models.CASCADE)

    def validate(self):
        """Checks that this Grant is still valid, perhaps by using it to
        authenticate against the external API."""
        raise NotImplementedError("Grant.validate")

    class Meta:
        abstract = True
