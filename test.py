import unittest

from requests import session
from ilo_scripting_helper import iLOSession, extract_ip_from_string

cases = [
    {'ip': "http://10.188.1.191/",
     'user': 'v0163usradmin',
     'password': 'HP!nvent123',
     'clean_ip': "10.188.1.191",
     "url_https": "https://10.188.1.191/",
     "url_API_https": "https://10.188.1.191/redfish/v1/",
     "gen": iLOSession.Generation.GEN9,
     "model": "ProLiant DL360 Gen9",
     "full_ilo_version": "iLO 4 v2.78",
     "ilo_version": iLOSession.iLOVersion.ILO_4,
     "ilo_firmware_version": "v2.78"
     },
    {'ip': "http://10.188.1.183/",
     'user': 'v0163usradmin',
     'password': 'HP!nvent123',
     'clean_ip': "10.188.1.183",
     "url_https": "https://10.188.1.183/",
     "url_API_https": "https://10.188.1.183/redfish/v1/",
     "gen": iLOSession.Generation.GEN10,
     "model": "ProLiant DL360 Gen10",
     "full_ilo_version": "iLO 5 v2.65",
     "ilo_version": iLOSession.iLOVersion.ILO_5,
     "ilo_firmware_version": "v2.65"
     },
    {'ip': "http://10.188.2.33/",
     'user': 'v0163usradmin',
     'password': 'HP!nvent123',
     'clean_ip': "10.188.2.33",
     "url_https": "https://10.188.2.33/",
     "url_API_https": "https://10.188.2.33/redfish/v1/",
     "gen": iLOSession.Generation.GEN10P,
     "model": "ProLiant DL360 Gen10 Plus",
     "full_ilo_version": "iLO 5 v2.70",
     "ilo_version": iLOSession.iLOVersion.ILO_5,
     "ilo_firmware_version": "v2.70"
     }
]


class TestIloScriptingTools(unittest.TestCase):
    def test_extract_ip_from_string(self):
        # cases = [{'test': "http://192.168.1.1/",
        #          'result': "192.168.1.1"},
        #          {'test': "http://192.168.1.1/",
        #          'result': "192.168.1.1"}
        #          ]

        for case in cases:
            with self.subTest(case['ip']):
                result = extract_ip_from_string(case['ip'])
                self.assertEqual(result, case['clean_ip'])

    # def test_create_session(self):
    #     try:
    #         createSession(extract_ip_from_string(
    #             "http://10.188.1.191/"), "v0163usradmin", "HP!nvent123")
    #     except:
    #         self.fail()

    # def test_get_server_generation(self):

    #     # cases = [{'ip': "http://10.188.1.191/", 'user': 'v0163usradmin', 'password': 'HP!nvent123',
    #     #           'result': Generation.GEN9},
    #     #          {'ip': "http://10.188.1.183/", 'user': 'v0163usradmin', 'password': 'HP!nvent123',
    #     #           'result': Generation.GEN10},
    #     #          {'ip': "http://10.188.2.33/", 'user': 'v0163usradmin', 'password': 'HP!nvent123',
    #     #           'result': Generation.GEN10P}
    #     #          ]
    #     for case in cases:
    #         with self.subTest(case['ip']):
    #             session = createSession(
    #                 extract_ip_from_string(case['ip']), case['user'], case['password'])

    #             result = get_server_generation(
    #                 session, extract_ip_from_string(case['ip']))
    #             self.assertEqual(result, case['result'])

    # def test_ilo_session_class(self):
    #     cases = [{'ip': "http://10.188.1.191/", 'user': 'v0163usradmin', 'password': 'HP!nvent123'},
    #              {'ip': "http://10.188.1.183/", 'user': 'v0163usradmin',
    #                  'password': 'HP!nvent123'},
    #              {'ip': "http://10.188.2.33/", 'user': 'v0163usradmin', 'password': 'HP!nvent123'}]
    #     for case in cases:
    #         with self.subTest(case['ip']):
    #             try:
    #                 session = iLOSession(
    #                     case['ip'], case['user'], case['password'])
    #             except:
    #                 self.fail(case["ip"])

    # def test_get_ilo_firmware_version():
    def test_ilo_session_power_metric(self):
        for case in cases:
            with self.subTest(case['ip']):
                session = iLOSession(
                    case['ip'], case['user'], case['password'])
                self.assertTrue(isinstance(session.get_power_metric(), int))

    def test_ilo_session_class_attributes(self):
        for case in cases:
            with self.subTest(case['ip']):
                session = iLOSession(
                    case['ip'], case['user'], case['password'])
                self.assertFalse(
                    session.ip != case["clean_ip"], session.ip + " != " + case["clean_ip"])
                self.assertFalse(
                    session.full_url != case["url_https"], session.full_url + " != " + case["url_https"])
                self.assertFalse(
                    session.API_url != case["url_API_https"], session.API_url + " != " + case["url_API_https"])
                self.assertFalse(
                    session.model != case["model"], session.model + " != " + case["model"])
                self.assertFalse(
                    session.full_ilo_version_string != case["full_ilo_version"], session.full_ilo_version_string + " != " + case["full_ilo_version"])
                self.assertFalse(
                    session.ilo_version != case["ilo_version"], session.ilo_version.name + " != " + case["ilo_version"].name)
                self.assertFalse(
                    session.ilo_firmware_version != case["ilo_firmware_version"], session.ilo_firmware_version + " != " + case["ilo_firmware_version"])
