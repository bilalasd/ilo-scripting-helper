import unittest
# from ilo_scripting_helper2 import iLOSession, extract_ip_from_string
import ilo_scripting_helper

cases = [
    {'ip': "http://10.188.1.191/",
     'user': 'v0163usradmin',
     'password': 'HP!nvent123',
     'clean_ip': "10.188.1.191",
     "url_https": "https://10.188.1.191/",
     "url_API_https": "https://10.188.1.191/redfish/v1/",
     "gen": ilo_scripting_helper.iLOSession.GENERATION.GEN9,
     "model": "ProLiant DL360 Gen9",
     "full_ilo_version": "iLO 4 v2.78",
     "ilo_version": ilo_scripting_helper.iLOSession.ILO_VERSION.ILO_4,
     "ilo_firmware_version": "v2.78"
     },
    {'ip': "http://10.188.1.183/",
     'user': 'v0163usradmin',
     'password': 'HP!nvent123',
     'clean_ip': "10.188.1.183",
     "url_https": "https://10.188.1.183/",
     "url_API_https": "https://10.188.1.183/redfish/v1/",
     "gen": ilo_scripting_helper.iLOSession.GENERATION.GEN10,
     "model": "ProLiant DL360 Gen10",
     "full_ilo_version": "iLO 5 v2.65",
     "ilo_version": ilo_scripting_helper.iLOSession.ILO_VERSION.ILO_5,
     "ilo_firmware_version": "v2.65"
     },
    {'ip': "http://10.188.2.33/",
     'user': 'v0163usradmin',
     'password': 'HP!nvent123',
     'clean_ip': "10.188.2.33",
     "url_https": "https://10.188.2.33/",
     "url_API_https": "https://10.188.2.33/redfish/v1/",
     "gen": ilo_scripting_helper.iLOSession.GENERATION.GEN10P,
     "model": "ProLiant DL360 Gen10 Plus",
     "full_ilo_version": "iLO 5 v2.70",
     "ilo_version": ilo_scripting_helper.iLOSession.ILO_VERSION.ILO_5,
     "ilo_firmware_version": "v2.70"
     }
]


class TestIloScriptingTools(unittest.TestCase):
    def test_extract_ip_from_string(self):

        for case in cases:
            with self.subTest(case['ip']):
                result = extract_ip_from_string(case['ip'])
                self.assertEqual(result, case['clean_ip'])

    def test_ilo_session_power_metric(self):
        for case in cases:
            with self.subTest(case['ip']):
                session = ilo_scripting_helper.iLOSession(
                    case['ip'], case['user'], case['password'])
                self.assertTrue(isinstance(session.get_power_metric(), int))

    def test_ilo_session_class_attributes(self):
        for case in cases:
            with self.subTest(case['ip']):
                session = ilo_scripting_helper.iLOSession(
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

    def test_environment_info(self):
        self.assertFalse("Windows-10-10.0.18363-SP0" != ilo_scripting_helper.EnvironmentInfo.get_system_platform_full_name(),
                         "Windows-10-10.0.18363-SP0" + "!=" + ilo_scripting_helper.EnvironmentInfo.get_system_platform_full_name())
        self.assertFalse(ilo_scripting_helper.EnvironmentInfo.OS.WINDOWS != ilo_scripting_helper.EnvironmentInfo.get_system_platform(
        ), ilo_scripting_helper.EnvironmentInfo.OS.WINDOWS.name + " != " + ilo_scripting_helper.EnvironmentInfo.get_system_platform().name)

    def test_timestamped_filename(self):
        with self.subTest("default"):
            temp = ilo_scripting_helper.get_timestamped_file_name("first","second","third")
            self.assertTrue(temp.endswith("first-second-third.txt"))

        with self.subTest("delimer ,"):
            temp = ilo_scripting_helper.get_timestamped_file_name("first","second","third",delimeter=",")
            self.assertTrue(temp.endswith("first,second,third.txt"))
        
        with self.subTest("delimer ,"):
            temp = ilo_scripting_helper.get_timestamped_file_name("first","second","third",delimeter=",",include_dot_txt=False)
            self.assertTrue(temp.endswith("first,second,third"))