from django.conf import settings
from .scanner_model import Scanner

from os2datascanner.engine2.model.sbsys import SbsysSource


class SbsysScanner(Scanner):
    def get_type(self):
        return 'sbsys'

    def get_absolute_url(self):
        return '/sbsysscanners'

    def generate_sources(self):
        yield SbsysSource(
            client_id=settings.SBSYS_CLIENT_ID,
            client_secret=settings.SBSYS_CLIENT_SECRET,
            token_url=settings.SBSYS_TOKEN_URL,
            api_url=settings.SBSYS_API_URL
        )
