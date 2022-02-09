import random
import requests
import uuid
import unittest
import json
from os2datascanner.engine2.rules.cpr import CPRRule


class WebScanIntegrationTest(unittest.TestCase):

    def test_scan_finds_all_sources(self):
        """Tests whether a scan finds all matches in a websource."""
        # create scans
        scanner_objects = {}
        amount_of_scans = 1
        actual_matches = 0
        expected_matches = 0

        for _ in range(amount_of_scans):
            seed = str(uuid.uuid1())
            matches = random.randrange(1, 500)
            expected_matches += matches
            sub_files = random.randrange(1, 20)
            response = requests.get(
                    "http://datasynth:5010/websource"
                    + f"?seed={seed}&sub_files={sub_files}"
                    + '&matches={"010180-0008":' + str(matches) + '}'
                    ).json()
            scan_url = response["reference"]
            scanner_objects[seed] = {
                "scan_name": seed, "scan_url": scan_url,
                "matches": matches, "sub_files": sub_files}

            headers = {
                'accept': 'application/jsonl',
                'Authorization': 'Bearer thisIsNotASecret',
                'Content-Type': 'application/json',
            }
            data = '{"url":'f'"{scan_url}"'+'}'

            response = requests.post(
                'http://api_server:5000/parse-url/1',
                headers=headers,
                data=data)

            self.assertEqual(response.status_code, 200, response.content)

            source = response.json()["source"]
            print(f"\nScan url: {source['url']}\n\n")

            rule = CPRRule()
            rule.BLACKLIST_WORDS = None
            rule = rule.to_json_object()
            data = json.dumps({"rule": rule, "source": source})

            response = requests.post('http://api_server:5000/scan/1', headers=headers, data=data)

            self.assertEqual(response.status_code, 200, response.content)

            messages = response.content.decode("utf-8")
            # we need to parse the incoming data as it is not properly json formatted
            messages = messages.split('}\n{')
            source_matches = 0
            for i in range(len(messages)):
                msg = messages[i]
                if i == 0:
                    msg = msg + "}"
                elif i == len(messages)-1:
                    msg = "{" + msg
                else:
                    msg = "{" + msg + "}"
                source_matches += self.parse_msg(msg)
            actual_matches += source_matches

        self.assertEquals(
            actual_matches,
            expected_matches,
            f"found matches: {actual_matches}, expected: {expected_matches}")

    def parse_msg(self, msg):
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

            print(f"found {no_matches} on {source}{path}")
        return no_matches

    def find_matches(self, list_dict):
        matches = 0
        for item in list_dict:
            if "matches" in item and (match_list := item["matches"]):
                matches += len(match_list)
        return matches
