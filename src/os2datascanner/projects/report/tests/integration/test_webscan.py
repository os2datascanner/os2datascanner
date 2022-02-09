import random
import requests
import uuid
import unittest
import json
from os2datascanner.engine2.rules.cpr import CPRRule


class WebScanTest(unittest.TestCase):
    """ Tests the webscans and their results"""

    def test_web_scan(self):
        """ A webscan should find all matches in a given source"""
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = random.randrange(10, 20)
        scan = self.create_scan(expected_matches, seed, sub_files)
        source_params = {}
        response = self.start_scan(scan, source_params)

        messages = response.content.decode("utf-8")
        match_locations = self.parse_api_response(messages)
        actual_matches = sum(match_locations.values())

        self.assertEqual(
            actual_matches, expected_matches,
            "the scan did not find all matches \n"
            + f"Scan Location:Match index = \n{match_locations}")

    def test_web_scan_with_excluded_file(self):
        """ A webscan with an exluded file, should not scan that file"""
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = random.randrange(0, 20)

        scan_1 = self.create_scan(expected_matches, seed, sub_files)
        response_1 = self.start_scan(scan_1, {})
        messages_1 = response_1.content.decode("utf-8")
        match_locations_1 = self.parse_api_response(messages_1)
        excluded_file = random.choice(list(match_locations_1.keys()))

        scan_2 = self.create_scan(expected_matches, seed, sub_files)
        source_params_2 = {"exclude": [excluded_file]}
        response_2 = self.start_scan(scan_2, source_params_2)
        messages_2 = response_2.content.decode("utf-8")
        match_locations_2 = self.parse_api_response(messages_2)

        self.assertNotIn(excluded_file, match_locations_2,
                         "the excluded file was found in the scan")

    def test_web_scan_with_last_modified(self):
        """ A webscan with last modified should find
        the same matches as one without"""
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = random.randrange(1, 15)

        scan_1 = self.create_scan(expected_matches, seed, sub_files)
        response_1 = self.start_scan(scan_1, {})
        messages_1 = response_1.content.decode("utf-8")
        match_locations_1 = self.parse_api_response(messages_1)
        first_scan_matches = sum(match_locations_1.values())

        source_params = {"last_modified": True}
        scan_2 = self.create_scan(expected_matches, seed, sub_files)
        response_2 = self.start_scan(scan_2, source_params)
        messages_2 = response_2.content.decode("utf-8")
        match_locations_2 = self.parse_api_response(messages_2)
        actual_matches = sum(match_locations_2.values())

        self.assertEqual(
            actual_matches, expected_matches,
            "the last modified scan did not find all matches \n"
            + f"Scan 1 Location:Match index = \n{match_locations_1}"
            + f"Scan 2 Location:Match index = \n{match_locations_2}")
        self.assertEqual(
            actual_matches, first_scan_matches,
            "the two scans found different amount of matches \n"
            + f"Scan 1 Location:Match index = \n{match_locations_1}"
            + f"Scan 2 Location:Match index = \n{match_locations_2}")

    def test_web_scan_with_last_modified_and_excluded_file(self):
        """ A webscan with an excluded file and last modified,
        should not scan that file but contain"""
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = random.randrange(0, 20)
        scan = self.create_scan(expected_matches, seed, sub_files)
        source_params_1 = {}
        response_1 = self.start_scan(scan, source_params_1)

        messages_1 = response_1.content.decode("utf-8")
        match_locations_1 = self.parse_api_response(messages_1)
        scan_matches_1 = sum(match_locations_1.values())

        # we don't want to exclude the base url
        excluded_file = random.choice(list(match_locations_1.keys()))
        while excluded_file == scan["scan_url"]:
            excluded_file = random.choice(list(match_locations_1.keys()))

        scan = self.create_scan(expected_matches, seed, sub_files)
        source_params_2 = {"exclude": [excluded_file], "last_modified": True}
        response_2 = self.start_scan(scan, source_params_2)

        messages_2 = response_2.content.decode("utf-8")
        match_locations_2 = self.parse_api_response(messages_2)
        scan_matches_2 = sum(match_locations_2.values())

        # subtract the matches contained in the excluded file and the excluded files sub_files
        # find the excluded_files seed (it will propagate down all children nodes/sub_files)
        excluded_file_seed = excluded_file.split("?seed=")[1].split("&")[0]
        excluded_matches = 0
        for match_location in match_locations_1:
            if excluded_file_seed in match_location:
                excluded_matches -= match_locations_1[match_location]

        self.assertNotIn(excluded_file, match_locations_2)
        self.assertEqual(scan_matches_1, scan_matches_2 + excluded_matches)

    def test_web_scan_with_sitemap(self):
        """ A webscan should find all matches in a given source"""
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = 2  # random.randrange(0, 20)
        scan = self.create_scan(expected_matches, seed, sub_files)
        source_params = {"sitemap": f"{scan['scan_url']}sitemap.xml"}
        response = self.start_scan(scan, source_params)
        messages = response.content.decode("utf-8")
        match_locations = self.parse_api_response(messages)
        # remove matches found on landing page, as these are not included in the count for
        # the index page
        match_locations.pop(scan["scan_url"])
        actual_matches = sum(match_locations.values())

        self.assertEqual(
            actual_matches, expected_matches,
            "the scan did not find all matches \n"
            + f"Scan Location:Match index = \n{match_locations}")

    def test_web_scan_with_sitemap_and_excluded_file(self):
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = random.randrange(1, 20)

        scan_1 = self.create_scan(expected_matches, seed, sub_files)
        source_params = {"sitemap": f"{scan_1['scan_url']}sitemap.xml"}
        response = self.start_scan(scan_1, source_params)
        messages = response.content.decode("utf-8")
        match_locations_1 = self.parse_api_response(messages)
        match_locations_1.pop(scan_1["scan_url"])

        excluded_file = random.choice(list(match_locations_1.keys()))

        scan_2 = self.create_scan(expected_matches, seed, sub_files)
        source_params_2 = {
            "exclude": [excluded_file],
            "sitemap": f"{scan_2['scan_url']}sitemap.xml"}
        response_2 = self.start_scan(scan_2, source_params_2)
        messages_2 = response_2.content.decode("utf-8")
        match_locations_2 = self.parse_api_response(messages_2)
        match_locations_2.pop(scan_2["scan_url"])

        self.assertNotIn(
            excluded_file,
            match_locations_2,
            f"the excluded file {excluded_file} is found in the second scan \n" +
            f"Scan Location:Match index = \n{match_locations_2=},\n{match_locations_1=}")

    def test_web_scan_with_sitemap_and_last_modified(self):
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = 2  # random.randrange(1, 15)

        scan_1 = self.create_scan(expected_matches, seed, sub_files)
        source_params_1 = {"sitemap": f"{scan_1['scan_url']}sitemap.xml"}
        response_1 = self.start_scan(scan_1, source_params_1)
        messages_1 = response_1.content.decode("utf-8")
        match_locations_1 = self.parse_api_response(messages_1)
        match_locations_1.pop(scan_1["scan_url"])
        first_scan_matches = sum(match_locations_1.values())

        source_params_2 = {"sitemap": f"{scan_1['scan_url']}sitemap.xml", "last_modified": True}
        scan_2 = self.create_scan(expected_matches, seed, sub_files)
        response_2 = self.start_scan(scan_2, source_params_2)
        messages_2 = response_2.content.decode("utf-8")
        match_locations_2 = self.parse_api_response(messages_2)
        match_locations_2.pop(scan_2["scan_url"])
        actual_matches = sum(match_locations_2.values())

        self.assertEqual(
            actual_matches, expected_matches,
            "the last modified scan did not find all matches \n"
            + f"Scan 1 Location:Match index = \n{match_locations_1}"
            + f"Scan 2 Location:Match index = \n{match_locations_2}")
        self.assertEqual(
            actual_matches, first_scan_matches,
            "the two scans found different amount of matches \n"
            + f"Scan 1 Location:Match index = \n{match_locations_1}"
            + f"Scan 2 Location:Match index = \n{match_locations_2}")

    def test_web_scan_with_sitemap_with_last_modified_and_excluded_file(self):
        """ A webscan with an excluded file and last modified and a sitemap,
        should not scan the excluded file but should find the rest of the matches"""
        seed = str(uuid.uuid1())
        expected_matches = 1000
        sub_files = random.randrange(0, 20)

        scan_1 = self.create_scan(expected_matches, seed, sub_files)
        source_params_1 = {"sitemap": f"{scan_1['scan_url']}sitemap.xml"}
        response_1 = self.start_scan(scan_1, source_params_1)
        messages_1 = response_1.content.decode("utf-8")
        match_locations_1 = self.parse_api_response(messages_1)
        match_locations_1.pop(scan_1["scan_url"])
        scan_matches_1 = sum(match_locations_1.values())

        # we don't want to exclude the base url
        excluded_file = random.choice(list(match_locations_1.keys()))
        while excluded_file == scan_1["scan_url"]:
            excluded_file = random.choice(list(match_locations_1.keys()))

        scan_2 = self.create_scan(expected_matches, seed, sub_files)

        source_params_2 = {"sitemap": f"{scan_2['scan_url']}sitemap.xml",
                           "exclude": [excluded_file],
                           "last_modified": True}

        response_2 = self.start_scan(scan_2, source_params_2)
        messages_2 = response_2.content.decode("utf-8")
        match_locations_2 = self.parse_api_response(messages_2)
        match_locations_2.pop(scan_2["scan_url"])
        scan_matches_2 = sum(match_locations_2.values())

        # subtract the matches contained in the excluded file and the excluded files sub_files
        # find the excluded_files seed (it will propagate down all children nodes/sub_files)
        excluded_file_seed = excluded_file.split("?seed=")[1].split("&")[0]
        excluded_matches = 0
        for match_location in match_locations_1:
            if excluded_file_seed in match_location:
                excluded_matches += match_locations_1[match_location]

        self.assertNotIn(excluded_file, match_locations_2,
                         f"the excluded file {excluded_file} is found in the second scan \n"
                         + f"Scan Location:Match index = \n{match_locations_2}")
        self.assertEqual(scan_matches_1 - excluded_matches, scan_matches_2,
                         f"the excluded file {excluded_file} is not found in the second scan, "
                         + "but the amount of matches does not match\nScan Location:Match index ="
                         + f"\n{match_locations_2=},\n{match_locations_1=}")

    def parse_api_response(self, messages):
        """ Formats the messages from the api so that it can
            be eaten properly by the parse_json msg"""
        # we need to parse the incoming data as it is not properly json formatted
        messages = messages.split('}\n{')
        match_locations = {}
        for i in range(len(messages)):
            msg = messages[i]
            if i == 0:
                msg = msg + "}"
            elif i == len(messages)-1:
                msg = "{" + msg
            else:
                msg = "{" + msg + "}"
            location, matches = self.parse_json(msg)
            if location is not None:
                if location in match_locations:
                    match_locations[location] += int(matches)
                else:
                    match_locations[location] = int(matches)
        return match_locations

    def parse_json(self, msg):
        """ Parses a json message to find path and matches """
        no_matches = 0
        message = json.loads(msg)
        if message['origin'] == "os2ds_matches":
            no_matches = self.find_matches(message["matches"])
            source = message['handle']['source']
            if source['type'] == 'web':
                source = source['url']
                path = message['handle']['path']
            elif source['type'] == 'pdf-page':
                source = source['handle']['source']['handle']
                path = source['path']
                source = source['source']['url']
            return source+path, no_matches
        else:
            return None, None

    def create_scan(self, matches, seed, sub_files):
        response = requests.get(
                    "http://datasynth:5010/websource"
                    + f"?seed={seed}&sub_files={sub_files}"
                    + '&matches={"010180-0008":' + str(matches) + '}'
                    ).json()
        scan_url = response["reference"]
        scan = {
            "scan_name": seed, "scan_url": scan_url,
            "matches": matches, "sub_files": sub_files}
        return scan

    def start_scan(self, scan, source_params=None):
        """ Creates and starts a webscan, returns the scan and
            the messages received from the api"""
        if source_params is None:
            source_params = {}
        headers = {
            'accept': 'application/jsonl',
            'Authorization': 'Bearer thisIsNotASecret',
            'Content-Type': 'application/json',
        }
        data = '{"url":'f'"{scan["scan_url"]}"'+'}'
        response = requests.post(
                'http://api_server:5000/parse-url/1',
                headers=headers,
                data=data)
        if response.status_code != 200:
            raise AssertionError(response.content)

        source = response.json()["source"]
        for param in source_params:
            source[param] = source_params[param]

        rule = CPRRule()
        rule = rule.to_json_object()
        rule["blacklist"] = ""

        data = json.dumps({"rule": rule, "source": source})
        api_response = requests.post('http://api_server:5000/scan/1', headers=headers, data=data)

        if api_response.status_code != 200:
            raise AssertionError(api_response.content)

        return api_response

    def find_matches(self, list_dict):
        """Counts all matches"""
        matches = 0
        for item in list_dict:
            if "matches" in item and (match_list := item["matches"]):
                matches += len(match_list)
        return matches
