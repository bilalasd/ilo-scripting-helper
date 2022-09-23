from enum import Enum
# import enum
import platform
import re
import time
import requests
import json

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_timestamped_file_name(*args, delimeter="-", include_dot_txt = True):
    returnString = time.strftime("[%Y:%m:%d-%H:%M:%S]")

    if len(args) == 0:
        raise Exception("AT LEAST ONE ARGUMENT IS REQUIRED")
    elif len(args) == 1:
        return returnString + args[0]
    else:
        for i in range(0, len(args) - 1):
            returnString += args[i] + delimeter
        returnString += args[len(args) - 1]
        if include_dot_txt:
            returnString += ".txt"
        return returnString


def extract_ip_from_string(unformattedString: str):
    """Extracts the ip from a given string. Uses regex

    Args:
        unformattedString (str): String which contains an ip. Can have multiple ip's but only the first one will be returned. Returned None if no ip is found.

    Returns:
        Str: Extracted ip in string format.
    """
    result = re.findall(
        "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)", unformattedString)
    if len(result) > 0:
        return result[0]
    else:
        return None


class EnvironmentInfo():

    class OS(Enum):
        LINUX = "Linux"
        WINDOWS = "Windows"

    @staticmethod
    def get_system_platform():
        temp = platform.system()
        if platform.system() == "Linux":
            return EnvironmentInfo.OS.LINUX
        else:
            return EnvironmentInfo.OS.WINDOWS

    @staticmethod
    def get_system_platform_full_name():
        temp = platform.system()
        if temp == "Linux":
            return platform.linux_distribution()
        else:
            return platform.platform()

    @staticmethod
    def get_python_version():
        return platform.python_version()


def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


class iLOSession():

    class GENERATION(Enum):
        GEN9 = "9"
        GEN10 = "10"
        GEN10P = "10p"

    class ILO_VERSION(Enum):
        ILO_4 = "ilo_4"
        ILO_3 = "ilo_3"
        ILO_5 = "ilo_5"

    def __init__(self, url, username, password, useHTTPS=True):
        """Provides many of the commonly used functions when scripting for iLO. Automatically gets many of the information that is used commonly such as BIOS settings, server generation etc.

        Args:
            url (str, required): Url or the ip of iLO. Can be in any format as long as there is an ip in the given string. Internally uses ilo_scripting_helper.extract_ip_from_string().
            username (str, required): Username of the iLO
            password (str, required): Password of the iLO
            useHTTPS (bool, optional): Uses the https:// protocol when true and http:// when false. Defaults to True.
        """

        self.username = username
        self.password = password
        self.ip = extract_ip_from_string(url)

        self._url_http = "http://" + self.ip + "/"
        self._url_https = "https://" + self.ip + "/"
        self.full_url = self._url_https if useHTTPS else self._url_http

        self._url_API_http = "http://" + self.ip + "/redfish/v1/"
        self._url_API_https = "https://" + self.ip + "/redfish/v1/"
        self.API_url = self._url_API_https if useHTTPS else self._url_API_http

        self.request_session = self.create_session()
        (self.model, self.generation) = self.get_server_generation()
        # self.model = self.get_server_model()
        self.BIOS_settings = self.get_BIOS_settings()

        (self.full_ilo_version_string, self.ilo_version,
         self.ilo_firmware_version) = self.get_ilo_version()

    def __del__(self):
        self.request_session.close()
    # TODO: def get_logical_drive_configuration
    # TODO: def delete_logical_drives
    # TODO: dec create_logical_drives
    # def get_power_reading():

    def create_session(self):
        """Creates a requests.Session() object. Gets called automatically when the iLOSession object is created. Rarely needs to be run directly.

        Raises:
            INVALID_CREDENTIALS: Raised when the provided credentials are wrong
            TOO_MANY_LOGIN_ATTEMPTS: Raised when multiple login attempts are made in a short amount of time.
            TOO_MANY_OPEN_SESSIONS: Raised when there are too many sessions open for the server.
            INVALID_RESPONSE_RECEIVED_FROM_SERVER: Raised when an invalid response is received while making a login attempt to iLO. Accompanies the actual message received from iLO.

        Returns:
            requests.Session(): requests.Session() object to be used to maked API calls
        """
        session = requests.Session()
        session.verify = False
        credentials = {
            "UserName": self.username,
            "Password": self.password
        }
        response = ""
        response = session.post(self.API_url + "SessionService/Sessions/",
                                json=credentials,  headers={'Content-Type': 'application/json'})
        if response.status_code != 201:
            if response.status_code == 400:
                if "UnauthorizedLoginAttempt" in json.loads(response.text)["error"]["@Message.ExtendedInfo"][0]["MessageId"]:
                    raise Exception("INVALID_CREDENTIALS")
                elif "LoginAttemptDelayed" in json.loads(response.text)["error"]["@Message.ExtendedInfo"][0]["MessageId"]:
                    raise Exception("TOO_MANY_LOGIN_ATTEMPTS")
                elif "CreateLimitReachedForResource" in json.loads(response.text)["error"]["@Message.ExtendedInfo"][0]["MessageId"]:
                    raise Exception("TOO_MANY_OPEN_SESSIONS")
                else:
                    raise Exception(
                        "INVALID_RESPONSE_RECEIVED_FROM_SERVER " + response.text)
        token = response.headers["X-Auth-Token"]
        session.headers.update({"X-Auth-Token": token})
        return session

    def get_ilo_version(self):
        response = self.request_session.get(
            self.API_url + 'Managers/1/').json()
        if self.generation == iLOSession.GENERATION.GEN9:
            full_version_string = response["Firmware"]["Current"]["VersionString"]
        else:
            full_version_string = response["FirmwareVersion"]
        temp = full_version_string.split(" ")
        if temp[1] == "4":
            ilo_version = iLOSession.ILO_VERSION.ILO_4
        elif temp[1] == "5":
            ilo_version = iLOSession.ILO_VERSION.ILO_5
        elif temp[1] == "3":
            ilo_version = iLOSession.ILO_VERSION.ILO_3
        ilo_firmware_version = temp[2]

        # root = ET.fromstring(x.content)
        return (full_version_string, ilo_version, ilo_firmware_version)

    def get_BIOS_settings(self):
        """Retrieves the BIOS setting for the server. Gets called automatically when the iLOSession object is created. Rarely needs to be run directly.

        Returns:
            Dict: Dictionary of all the BIOS settings on the server
        """

        if self.generation is self.GENERATION.GEN9:
            response = self.request_session.get(
                self.API_url + "systems/1/bios/settings/")
            currentSettings = response.json()

            response = self.request_session.get(
                self.API_url + "systems/1/bios/service/settings/")
            currentSettings = merge_two_dicts(currentSettings, response.json())
        else:
            response = self.request_session.get(
                self.API_url + "systems/1/bios/settings/")
            currentSettings = response.json()["Attributes"]

            if self.generation is self.GENERATION.GEN10:
                response = self.request_session.get(
                    self.API_url + "systems/1/bios/service/settings/")
                currentSettings = merge_two_dicts(
                    currentSettings, response.json()["Attributes"])
        return currentSettings

    def get_server_generation(self):
        """Retrieves the generation of the server

        Returns:
            Generation: iLOSession.Generation enum for the given generation.
        """

        response = self.request_session.get(
            self.API_url + "systems/1/")
        productJSON = response.json()
        model = productJSON["Model"]
        product = productJSON["Model"].lower()

        if "gen10 plus" in product:
            return (model, self.GENERATION.GEN10P)
        elif "gen10" in product:
            return (model, self.GENERATION.GEN10)
        elif "gen9" in product:
            return (model, self.GENERATION.GEN9)
        else:
            return None

    def get_power_metric(self):
        if self.ilo_version in [iLOSession.ILO_VERSION.ILO_4, iLOSession.ILO_VERSION.ILO_5]:
            response = self.request_session.get(
                self.API_url + 'chassis/1/power')
            responseJson = response.json()
            # print(responseJson['PowerControl'][0]['PowerConsumedWatts'])
            return responseJson['PowerControl'][0]['PowerConsumedWatts']
        else:
            raise Exception(
                "METHOD DOES NOT WORK ON THIS VERSION ILO. ILO VERSION: " + self.ilo_version.name)


if __name__ == '__main__':
    ses = iLOSession("10.188.1.191", "v0163usradmin", "HP!nvent123")
    print(type(ses.get_power_metric()))
