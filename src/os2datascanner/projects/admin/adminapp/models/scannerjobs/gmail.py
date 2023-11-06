import os
import json
from csv import DictReader

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .scanner import Scanner
from os2datascanner.engine2.model.gmail import GmailSource
from ...utils import upload_path_gmail_users, upload_path_gmail_service_account


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

    service_account_file_gmail = models.FileField(upload_to=upload_path_gmail_service_account,
                                                  null=False,
                                                  validators=[validate_filetype_json])

    user_emails_gmail = models.FileField(upload_to=upload_path_gmail_users,
                                         null=False,
                                         validators=[validate_filetype_csv])

    def get_type(self):
        return 'gmail'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/gmailscanners'

    def generate_sources(self):
        with open(os.path.join(settings.MEDIA_ROOT, self.service_account_file_gmail.name)) as saf:
            temp = json.load(saf)
        with open(os.path.join(settings.MEDIA_ROOT, self.user_emails_gmail.name), 'r') as usrem:
            csv_dict_reader = DictReader(usrem)
            for row in csv_dict_reader:
                user_email = row['Email Address [Required]']
                yield GmailSource(service_account_file_gmail=json.dumps(temp),
                                  user_email_gmail=user_email)
