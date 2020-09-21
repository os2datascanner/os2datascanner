from django.db import models
from django.core.exceptions import ValidationError
from .scanner_model import Scanner


class GmailScanner(Scanner):

    def validate_filetype_json(upload_file):
        extension = upload_file.name.split('.')[-1]
        if extension not in ['json']:
            raise ValidationError(
                'Forkert filformat! Upload venligst i json'
            )

    def validate_filetype_csv(upload_file):
        extension = upload_file.name.split('.')[-1]
        if extension not in ['csv']:
            raise ValidationError(
                'Forkert filformat! Upload venligst i csv \n'
                'csv fil hentes af admin fra: https://admin.google.com/ac/users'
            )

    service_account_file_gmail = models.FileField(upload_to='gmail/serviceaccount/',
                                                  null=False,
                                                  validators=[validate_filetype_json])

    user_emails_gmail = models.FileField(upload_to='gmail/users/',
                                         null=False,
                                         validators=[validate_filetype_csv])

    def __str__(self):
        """Return the URL for the scanner."""
        return self.url

    def get_type(self):
        return 'gmail'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/gmailscanners'

    def generate_sources(self):
        pass
