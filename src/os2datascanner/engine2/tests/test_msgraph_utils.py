"""
Unit tests for utilities for use with MS Graph.
"""

import requests
import unittest

from os2datascanner.engine2.model.msgraph import utilities as msgu
from os2datascanner.engine2.model.msgraph.graphiti import (builder,
                                                           baseclasses,
                                                           exceptions,
                                                           query_parameters)


class TestGraphUtilities(unittest.TestCase):
    def setUp(self):
        self._token = 1

    def _token_creator(self):
        self._token += 1

    def test_rrd(self):
        """The raw_request_decorator function implements retry logic
        correctly."""
        @msgu.raw_request_decorator
        def handle(self):
            response = requests.Response()
            match self._token:
                case 1:
                    response.status_code = 401
                case _:
                    response.status_code = 200
            return response

        self.assertEqual(
                handle(self).status_code,
                200,
                "didn't get the expected status code")


class TestMSGraphURLBuilder(unittest.TestCase):
    """
    Unit tests for the MSGraphURLBuilder utility class.
    """

    def setUp(self):
        self.builder = builder.MSGraphURLBuilder()
        self.uid = 'olsenbanden@microsoft.com'
        self.gid = 'olsenbandensfanklub'
        self.did = 'planer'
        self.eid = 'det-store-kup-mod-bang-johansen'
        self.mfid = 'hemmelige-oplysninger'
        self.nid = 'koden-til-pengeskabet'

    def test_default_builder_returns_base_url(self):
        # Arrange
        expected = baseclasses.BASE_URL

        # Act
        actual = self.builder.build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_endpoint(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0'

        # Act
        actual = self.builder.v1().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_beta_endpoint(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/beta'

        # Act
        actual = self.builder.beta().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_me(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/me'

        # Act
        actual = self.builder.v1().me().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_me_calendar(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/me/calendar'

        # Act
        actual = self.builder.v1().me().calendar().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_me_calendar_groups(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/me/calendarGroups'

        # Act
        actual = self.builder.v1().me().calendar_groups().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_me_calendar_view(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/me/calendarView'

        # Act
        actual = self.builder.v1().me().calendar_view().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_me_drive(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/me/drive'

        # Act
        actual = self.builder.v1().me().drive().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_with_id(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/users/{self.uid}'

        # Act
        actual = self.builder.v1().users(self.uid).build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_app_role_assignments(self):
        # Arrange
        expected = (baseclasses.BASE_URL +
                    f'/v1.0/users/{self.uid}/appRoleAssignments')

        # Act
        actual = self.builder.v1().users(self.uid).app_role_assignments().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_calendars(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/users/{self.uid}/calendars'

        # Act
        actual = self.builder.v1().users(self.uid).calendars().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_drives(self):
        # Arrange
        expected = (baseclasses.BASE_URL +
                    f'/v1.0/users/{self.uid}/drives/{self.did}')

        # Act
        actual = self.builder.v1().users(self.uid).drives(self.did).build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_events(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/users/{self.uid}/events/{self.eid}'

        # Act
        actual = self.builder.v1().users(self.uid).events(self.eid).build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_mail_folders(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/users/{self.uid}/mailFolders/{self.mfid}'

        # Act
        actual = self.builder.v1().users(self.uid).mail_folders(self.mfid).build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_users_onenote_notebook(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/users/{self.uid}/onenote/notebook/{self.nid}'

        # Act
        actual = self.builder.v1().users(self.uid).onenote().notebook(self.nid).build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_groups(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/groups/{self.gid}'

        # Act
        actual = self.builder.v1().groups(self.gid).build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_groups_sites(self):
        # Arrange
        expected = baseclasses.BASE_URL + f'/v1.0/groups/{self.gid}/sites'

        # Act
        actual = self.builder.v1().groups(self.gid).sites().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_sites_root(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/sites/root'

        # Act
        actual = self.builder.v1().sites().root().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_directory(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/directory'

        # Act
        actual = self.builder.v1().directory().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_directory_objects(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/directoryObjects'

        # Act
        actual = self.builder.v1().directory_objects().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_v1_drive(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0/drive'

        # Act
        actual = self.builder.v1().drive().build()

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_build_empty(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0'

        # Act
        odata = query_parameters.ODataQueryBuilder()
        node = self.builder.v1()
        actual = odata.build(node)

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_build_count(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0?$count=true'

        # Act
        odata = query_parameters.ODataQueryBuilder().count(True)
        node = self.builder.v1()
        actual = odata.build(node)

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_build_count_top(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0?$count=true&$top=1'

        # Act
        odata = query_parameters.ODataQueryBuilder().count(True).top(1)
        node = self.builder.v1()
        actual = odata.build(node)

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_twice_raises_error(self):
        # Act & Assert
        with self.assertRaises(exceptions.DuplicateODataParameterError):
            query_parameters.ODataQueryBuilder().count().count()

    def test_odata_count_invalid_type_raises_error(self):
        # Act & Assert
        with self.assertRaises(ValueError):
            query_parameters.ODataQueryBuilder().count('invalid argument')

    def test_odata_count_remove_count_is_ok(self):
        # Arrange
        expected = baseclasses.BASE_URL + '/v1.0?$count=true'

        # Act
        odata = query_parameters.ODataQueryBuilder().count().remove('count').count()
        node = self.builder.v1()
        actual = odata.build(node)

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_remove_invalid_key_type_raises_error(self):
        # Act & Assert
        with self.assertRaises(ValueError):
            query_parameters.ODataQueryBuilder().remove(42)

    def test_odata_to_url_empty(self):
        # Arrange
        expected = ''

        # Act
        actual = query_parameters.ODataQueryBuilder().to_url()

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_to_url_count(self):
        # Arrange
        expected = '?$count=true'

        # Act
        actual = query_parameters.ODataQueryBuilder().count().to_url()

        # Assert
        self.assertEqual(expected, actual)

    def test_odata_to_url_count_top(self):
        # Arrange
        expected = '?$count=true&$top=1'

        # Act
        actual = query_parameters.ODataQueryBuilder().count().top(1).to_url()

        # Assert
        self.assertEqual(expected, actual)
