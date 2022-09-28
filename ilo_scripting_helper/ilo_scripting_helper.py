from enum import Enum
from opcode import hasconst
import os
import platform
import re
import sys
import time
import requests
import json

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_timestamped_file_name(*args, delimeter="-", include_dot_txt=True):
    returnString = time.strftime("[%Y:%m:%d-%H:%M:%S]")

    if len(args) == 0:
        raise Exception("AT LEAST ONE ARGUMENT IS REQUIRED")
    elif len(args) == 1:
        returnString = returnString + args[0]
        if include_dot_txt:
            returnString += ".txt"
        return returnString
    else:
        for i in range(0, len(args) - 1):
            returnString += args[i] + delimeter
        returnString += args[len(args) - 1]
        if include_dot_txt:
            returnString += ".txt"
        return returnString


def read_in_values_from_file(file_name):
    if not os.path.exists(file_name):
        raise Exception(file_name + " DOESN'T EXISTS")
    values = []
    with open(file_name, "r") as fp:

        data = fp.read()
        rows = data.split("\n")

        for row in rows:
            if row.strip().replace(" ", "").replace("\t", "") == "":
                continue
            split = " ".join(row.split()).replace(" ", "\t").strip().split("\t")
            values.append(split)
    return values


def extract_ip_from_string(unformattedString: str):
    """Extracts the ip from a given string. Uses regex

    Args:
        unformattedString (str): String which contains an ip. Can have multiple ip's but only the first one will be returned. Returned None if no ip is found.

    Returns:
        Str: Extracted ip in string format.
    """
    result = re.findall(
        "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",
        unformattedString,
    )
    if len(result) > 0:
        return result[0]
    else:
        return None


def get_server_generation(ip, use_https=True):
    """Retrieves the generation of the server

    Returns:
        Generation: iLOSession.Generation enum for the given generation.
    """
    ip = extract_ip_from_string(ip)

    # response = self.request_session.get(
    #     self.API_url + "systems/1/")
    api_url = "https://" if use_https else "http://"
    api_url += ip + "/redfish/v1/systems/1/"
    response = requests.get(api_url, verify=False)
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


class EnvironmentInfo:
    class OS(Enum):
        LINUX = "Linux"
        WINDOWS = "Windows"
        DARWIN = "Darwin"

    @staticmethod
    def get_system_platform():
        temp = platform.system()
        if temp == "Linux":
            return EnvironmentInfo.OS.LINUX
        elif temp == "Darwin":
            return EnvironmentInfo.OS.DARWIN
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
    z = x.copy()  # start with keys and values of x
    z.update(y)  # modifies z with keys and values of y
    return z


class iLOSession:
    class GENERATION(Enum):
        GEN9 = "9"
        GEN10 = "10"
        GEN10P = "10p"

    class ILO_VERSION(Enum):
        ILO_4 = "ilo_4"
        ILO_3 = "ilo_3"
        ILO_5 = "ilo_5"

    class ILO4_RESET_OPTIONS(Enum):
        ON = "On"
        FORCE_OFF = "ForceOff"
        GRACEFUL_SHUTDOWN = "GracefulShutdown"
        FORCE_RESTART = "ForceRestart"
        NMI = "Nmi"
        PUSH_POWER_BUTTON = "PushPowerButton"
        GRACEFUL_RESTART = "GracefulRestart"

    class ILO4_RESET_OPTIONS(Enum):
        ON = "On"
        FORCE_OFF = "ForceOff"
        FORCE_RESTART = "ForceRestart"
        NMI = "Nmi"
        PUSH_POWER_BUTTON = "PushPowerButton"

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
        (self.model, self.generation) = self._get_server_generation()

        (
            self._bios_settings_pending,
            self._bios_service_settings_pending,
            self.bios_settings_pending,
            self._bios_settings_final,
            self._bios_service_settings_final,
            self.bios_settings_final,
        ) = self._get_bios_settings()

        (
            self.full_ilo_version_string,
            self.ilo_version,
            self.ilo_firmware_version,
        ) = self._get_ilo_version()

    def __del__(self):
        if hasattr(self, "request_session"):
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
        credentials = {"UserName": self.username, "Password": self.password}
        response = ""
        response = session.post(
            self.API_url + "SessionService/Sessions/",
            json=credentials,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 201:
            if response.status_code == 400:
                if "UnauthorizedLoginAttempt" in response.text:
                    raise Exception("INVALID_CREDENTIALS")
                elif "LoginAttemptDelayed" in response.text:
                    raise Exception("TOO_MANY_LOGIN_ATTEMPTS")
                elif "CreateLimitReachedForResource" in response.text:
                    raise Exception("TOO_MANY_OPEN_SESSIONS")
                else:
                    raise Exception(
                        "INVALID_RESPONSE_RECEIVED_FROM_SERVER " + response.text
                    )
        token = response.headers["X-Auth-Token"]
        session.headers.update({"X-Auth-Token": token})
        return session

    def reset_server(self, reset_option):
        if self.ilo_version == iLOSession.ILO_VERSION.ILO_3:
            raise Exception("iLO 3 NOT SUPPORTED")

        if self.ilo_version == iLOSession.ILO_VERSION.ILO_4:
            pass
            self.request_session.post(
                self.API_url + "Systems/1/",
                {"Action": "Reset", "ResetType": reset_option.name},
            )

        else:
            pass
            self.request_session.post(
                self.API_url + "Systems/1/Actions/ComputerSystem.Reset/",
                {"ResetType": reset_option.name},
            )

    def update_ilo_version(self):
        (
            self.full_ilo_version_string,
            self.ilo_version,
            self.ilo_firmware_version,
        ) = self._get_ilo_version()

    def _get_ilo_version(self):
        response = self.request_session.get(self.API_url + "Managers/1/").json()
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

    def update_bios_settings(self):
        (
            self._bios_settings_pending,
            self._bios_service_settings_pending,
            self.bios_settings_pending,
            self._bios_settings_final,
            self._bios_service_settings_final,
            self.bios_settings_final,
        ) = self._get_bios_settings()

    def _get_bios_settings(self):
        """Retrieves the BIOS setting for the server. Gets called automatically when the iLOSession object is created. Rarely needs to be run directly.

        Returns:
            Dict: Dictionary of all the BIOS settings on the server
        """
        # bios_settings = {}
        # bios_settings_pending = {}
        # bios_service_settings = {}
        # bios_service_settings_pending = {}
        # combined_settings = {}

        # final settings
        response = self.request_session.get(self.API_url + "systems/1/bios/").json()
        bios_settings_final = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # final service settings
        response = self.request_session.get(
            self.API_url + "systems/1/bios/service/"
        ).json()
        bios_service_settings_final = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # combine the two final settings
        combined_settings_final = merge_two_dicts(
            bios_settings_final, bios_service_settings_final
        )

        # pending settings
        response = self.request_session.get(
            self.API_url + "systems/1/bios/settings/"
        ).json()
        bios_settings_pending = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # pending service settings
        response = self.request_session.get(
            self.API_url + "systems/1/bios/service/settings/"
        ).json()
        bios_service_settings_pending = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # combine the two pending settings
        combined_settings_pending = merge_two_dicts(
            bios_settings_pending, bios_service_settings_pending
        )

        return (
            bios_settings_pending,
            bios_service_settings_pending,
            combined_settings_pending,
            bios_settings_final,
            bios_service_settings_final,
            combined_settings_final,
        )

    def update_bios_settings(self):
        (
            self._bios_settings_pending,
            self._bios_service_settings_pending,
            self.bios_settings_pending,
            self._bios_settings_final,
            self._bios_service_settings_final,
            self.bios_settings_final,
        ) = self._get_bios_settings()

    def _get_bios_settings(self):
        """Retrieves the BIOS setting for the server. Gets called automatically when the iLOSession object is created. Rarely needs to be run directly.

        Returns:
            Dict: Dictionary of all the BIOS settings on the server
        """
        # bios_settings = {}
        # bios_settings_pending = {}
        # bios_service_settings = {}
        # bios_service_settings_pending = {}
        # combined_settings = {}

        # final settings
        response = self.request_session.get(self.API_url + "systems/1/bios/").json()
        bios_settings_final = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # final service settings
        response = self.request_session.get(
            self.API_url + "systems/1/bios/service/"
        ).json()
        bios_service_settings_final = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # combine the two final settings
        combined_settings_final = merge_two_dicts(
            bios_settings_final, bios_service_settings_final
        )

        # pending settings
        response = self.request_session.get(
            self.API_url + "systems/1/bios/settings/"
        ).json()
        bios_settings_pending = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # pending service settings
        response = self.request_session.get(
            self.API_url + "systems/1/bios/service/settings/"
        ).json()
        bios_service_settings_pending = (
            response
            if self.generation == iLOSession.GENERATION.GEN9
            else response["Attributes"]
        )

        # combine the two pending settings
        combined_settings_pending = merge_two_dicts(
            bios_settings_pending, bios_service_settings_pending
        )

        return (
            bios_settings_pending,
            bios_service_settings_pending,
            combined_settings_pending,
            bios_settings_final,
            bios_service_settings_final,
            combined_settings_final,
        )

    def update_server_generation(self):
        (self.model, self.generation) = self.get_server_generation()

    def _get_server_generation(self):
        """Retrieves the generation of the server

        Returns:
            Generation: iLOSession.Generation enum for the given generation.
        """

        response = self.request_session.get(self.API_url + "systems/1/")
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

    def compare_bios_settings(self, values, use_pending=True):
        """_summary_

        Args:
            values (_type_): _description_

        Raises:
            Exception: _description_
            Exception: _description_

        Returns:
            _type_: _description_
        """
        if len(values) == 0:
            raise Exception("PROVIDED DICT IS EMPTY")

        return_obj = {}
        any_differences = False

        for key in values:
            val = values[key]

            if (
                key not in self.bios_settings_pending
                and key not in self._bios_service_settings_pending
            ):
                return_obj[key] = {
                    "setting_current_value": None,
                    "setting_new_value": val,
                    "comparison": None,
                    "found_in_bios": False,
                }
                continue
            current_bios_settings = (
                self.bios_settings_pending if use_pending else self.bios_settings_final
            )
            current_service_bios_settings = (
                self._bios_service_settings_pending
                if use_pending
                else self._bios_service_settings_final
            )

            if key in current_bios_settings:
                # value = "DIFFERENT" if val != current_bios_settings[key] else "SAME"
                is_different = "SAME"
                if val != current_bios_settings[key]:
                    is_different = "DIFFERENT"
                    any_differences = True

                return_obj[key] = {
                    "setting_current_value": current_bios_settings[key],
                    "setting_new_value": val,
                    "comparison": is_different,
                    "found_in_bios": True,
                }
            else:
                is_different = "SAME"
                if val != current_service_bios_settings[key]:
                    is_different = "DIFFERENT"
                    any_differences = True

                # value = "DIFFERENT" if val != current_service_bios_settings[key] else "SAME"

                return_obj[key] = {
                    "setting_current_value": current_service_bios_settings[key],
                    "setting_new_value": val,
                    "comparison": is_different,
                    "found_in_bios": True,
                }

        return (return_obj, any_differences)

    def get_power_metric(self):
        if self.ilo_version in [
            iLOSession.ILO_VERSION.ILO_4,
            iLOSession.ILO_VERSION.ILO_5,
        ]:
            response = self.request_session.get(self.API_url + "chassis/1/power")
            responseJson = response.json()
            # print(responseJson['PowerControl'][0]['PowerConsumedWatts'])
            return responseJson["PowerControl"][0]["PowerConsumedWatts"]
        else:
            raise Exception(
                "METHOD DOES NOT WORK ON THIS VERSION ILO. ILO VERSION: "
                + self.ilo_version.name
            )

    def change_bios_settings(self, values):
        if len(values) == 0:
            raise Exception("PROVIDED DICT IS EMPTY")

        new_bios_body = {
            "@odata.id": "/redfish/v1/systems/1/bios/settings/",
        }

        new_bios_service_body = {
            "@odata.id": "/redfish/v1/systems/1/bios/service/settings/"
        }

        if self.generation == iLOSession.GENERATION.GEN9:
            new_bios_body["Attributes"] = {}
            new_bios_service_body["Attributes"] = {}
        bios_settings_changed = False
        bios_service_settings_changed = False

        for key in values:
            val = values[key]

            if (
                key not in self.bios_settings_pending
                and key not in self._bios_service_settings_pending
            ):
                raise Exception("'" + val + "' NOT FOUND IN CURRENT BIOS SETTINGS")

            if self.generation == iLOSession.GENERATION.GEN9:
                if key in self.bios_settings_pending:
                    new_bios_body[key] = val
                    bios_settings_changed = True
                else:
                    new_bios_service_body[key] = val
                    bios_service_settings_changed = True
            else:
                if key in self.bios_settings_pending:
                    new_bios_body["Attributes"][key] = val
                    bios_settings_changed = True
                else:
                    new_bios_service_body["Attributes"][key] = val
                    bios_service_settings_changed = True

        if bios_settings_changed:
            response = self.request_session.patch(
                self.API_url + "Systems/1/bios/settings", json=new_bios_body
            )
            # test = response

        if bios_service_settings_changed:
            response = self.request_session.patch(
                self.API_url + "Systems/1/bios/service/settings",
                json=new_bios_service_body,
            )
            # test = response

        return


if __name__ == "__main__":
    print("This file should be run directly, import it into a project.")
    sys.exit
