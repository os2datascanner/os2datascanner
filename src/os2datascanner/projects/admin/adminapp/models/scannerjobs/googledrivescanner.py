import os
import json
from csv import DictReader

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .scanner import Scanner
from ...utils import upload_path_gdrive_users, upload_path_gdrive_service_account
from os2datascanner.engine2.model.googledrive import GoogleDriveSource


class GoogleDriveScanner(Scanner):

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

    service_account_file = models.FileField(upload_to=upload_path_gdrive_service_account,
                                            null=False,
                                            validators=[validate_filetype_json])

    user_emails = models.FileField(upload_to=upload_path_gdrive_users,
                                   null=False,
                                   validators=[validate_filetype_csv])

    def __str__(self):
        """Return the URL for the scanner."""
        return self.url

    def get_type(self):
        return 'googledrive'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/googledrivescanners'

    def generate_sources(self):
        with open(os.path.join(settings.MEDIA_ROOT, self.service_account_file.name)) as saf:
            temp = json.load(saf)
        with open(os.path.join(settings.MEDIA_ROOT, self.user_emails.name), 'r') as usrem:
            csv_dict_reader = DictReader(usrem)
            for row in csv_dict_reader:
                user_email = row['Email Address [Required]']
                yield GoogleDriveSource(service_account_file=json.dumps(temp),
                                        user_email=user_email)
