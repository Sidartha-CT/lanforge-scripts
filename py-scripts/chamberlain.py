from test_setup import (
    MGR,
    PORT,
    NO_OF_STATIONS,
    WIPHY_RADIO,
    UPSTREAM_PORT,
    TRAFFIC_TYPE,
    UPLOAD_RATE,
    DOWNLOAD_RATE,
    WPS_IP,
    WPS_USERNAME,
    WPS_PASSWORD,
    PING_TIME,
    WPS_OUTLETS,
    EXPECTED_PING_LOSS_WITHOUT_LOAD,
    EXPECTED_PING_LATENCY_WITHOUT_LOAD,
    EXPECTED_PING_LOSS_WITH_LOAD,
    EXPECTED_PING_LATENCY_WITH_LOAD,
    WPS_AP_NAMES,
    ROTATOR_WPS_NUMBER,
    ROTATOR_WPS_IP,
    IP_FETCH_INTERVAL,
    IP_FETCH_RETRIES,
    SSID,
    SECURITY,
    PASSWORD,
    DUT_NAME
)
from dict import (
    ADD_STA_FLAGS,
    ADD_STA_MODES,
    SET_PORT_INTREST_FLAGS,
    SET_PORT_CURRENT_FLAGS,
    WIFI_EXTRA_DATA,
    WIFI_EXTRA2_DATA,
    WIFI_TXO_DATA,
    RESET_PORT_EXTRA_DATA
)
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import lf_report
import logging
import threading
import requests
from urllib import request
import sys
import json
import urllib
import time
import traceback
import re
from pprint import pformat, PrettyPrinter
import datetime
import math
import wps
import subprocess
import pandas as pd
import datetime
import ipaddress
import shutil
# import time
import re
import os
debug_printer = PrettyPrinter(indent=2)

root = logging.getLogger()
root.handlers = []
root.setLevel(logging.CRITICAL)

# Create your own logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # accept all; handlers filter

log_format = logging.Formatter(
    '%(asctime)s %(levelname)-8s %(message)s %(filename)s %(lineno)s'
)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
debug_handler = logging.FileHandler("debug.log")
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(log_format)
logger.addHandler(console_handler)
logger.addHandler(debug_handler)

# Prevent logs bubbling up to root
logger.propagate = False

# PING_TIME = 60
MODE_2G = 15
# UPLOAD_RATE = "2"
# DOWNLOAD_RATE = "2"
# TRAFFIC_TYPE = "lf_tcp"
DEBUG = False
# TIME_GAP = 10


class JSON:
    def __init__(self, lanforge_ip="localhost", port=8080):
        """
        Initialize LANforge JSON API wrapper.

        Args:
            lanforge_ip (str): LANforge Manager IP address.
            port (int/str): LANforge port.

        Attributes:
            pre_url (str): Base URL for API requests.
            default_headers (dict): Default request headers for JSON calls.
            No_Data (dict): Placeholder for empty POST calls.
        """

        self.lanforge_ip = lanforge_ip
        self.port = port
        self.pre_url = "http://{}:{}/".format(lanforge_ip, port)
        self.default_headers = {'Accept': 'application/json'}
        self.No_Data = {'No Data': 0}

    # def encode_url(self, url):
    #     safe_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~:/?&="
    #     encoded = ""
    #     for ch in url:
    #         if ch in safe_chars:
    #             encoded += ch
    #         else:
    #             encoded += "%" + format(ord(ch), "02X")
    #     return encoded
    def port_down_request(self, resource_id, port_name, debug_on=False):
        """
        Does not change the use_dhcp flag
        See http://localhost:8080/help/set_port
        :param debug_on:
        :param resource_id:
        :param port_name:
        :return: json payload
        """
        REPORT_TIMER_MS_FAST = 1500
        data = {
            "shelf": 1,
            "resource": resource_id,
            "port": port_name,
            "current_flags": 1,  # vs 0x0 = interface up
            "interest": 8388610,  # = current_flags + ifdown
            "report_timer": REPORT_TIMER_MS_FAST,
        }
        logger.debug("PORT DOWN REQUEST")
        logger.debug("With data {}".format(data))
        if debug_on:
            logger.debug("Port down request")
            logger.debug(debug_printer.pformat(data))
        return data

    def encode_url(self, required_url):
        """
        Encode URL while preserving special API characters like '+' & ','.

        Args:
            required_url (str): URL to encode.

        Returns:
            str: Encoded URL safe for LANforge API calls.
        """
        safe_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~:/?&=+,"

        encoded = ""
        for ch in required_url:
            if ch in safe_chars:
                encoded += ch
            else:
                encoded += "%" + format(ord(ch), "02X")
        return encoded

    def get(self, url, method_='GET'):
        """
        Perform an HTTP GET request to LANforge.

        Args:
            url (str): API endpoint.
            method_ (str): HTTP method (default GET).

        Returns:
            HTTPResponse | None: Response object if successful, otherwise None.
        """
        if url[0] == '/':
            url = url[1:]
        req_url = self.pre_url + url
        # print('required url',req_url)
        try:
            myrequest = request.Request(url=self.encode_url(req_url),
                                        headers=self.default_headers,
                                        method=method_)
            myresponses = []
            myresponses.append(request.urlopen(myrequest))
            return myresponses[0]
        except BaseException:
            logger.debug("FAILED API CALL: {}".format(self.encode_url(req_url)))
            # print("bye")
            # exit(0)
            return None

    def get_as_json(self, url, method_='GET'):
        """
        Execute GET request and parse response JSON.

        Args:
            url (str): API endpoint for lanforge.
            method_ (str): HTTP method.

        Returns:
            dict | None: Parsed JSON data or None on failure.
        """
        responses = list()
        responses.append(self.get(url, method_=method_))
        if len(responses) < 1:
            return None
        if responses[0] is None:
            logger.debug("No response from " + url)
            return None
        json_data = json.loads(responses[0].read().decode('utf-8'))
        return json_data

    def addPostData(self, url, data, method_='POST', response_json_list_=None):
        """
        Send HTTP POST request with JSON body to LANforge.

        Args:
            url (str): API endpoint.
            data (dict): JSON data payload.
            method_ (str): HTTP method (default POST).
            response_json_list_ (list|None): Optional — append returned JSON here.

        Returns:
            HTTPResponse | None: Response object, or None on error.
        """
        self.post_data = data
        if url[0] == '/':
            url = url[1:]
        req_url = self.pre_url + url
        responses = []
        if data is not None and data is not self.No_Data:
            logger.debug("POST Data {}".format(self.post_data))
            logger.debug("url : {}".format(req_url))
            logger.debug("encode url: {}".format(self.encode_url(req_url)))
            myrequest = request.Request(url=self.encode_url(req_url),
                                        method=method_,
                                        data=json.dumps(self.post_data).encode("utf-8"),
                                        headers=self.default_headers)
        else:
            # print("without data")
            myrequest = request.Request(url=self.encode_url(req_url), headers=self.default_headers)

        myrequest.headers['Content-type'] = 'application/json'
        try:
            resp = urllib.request.urlopen(myrequest)
            resp_data = resp.read().decode('utf-8')
            responses.append(resp)
            if response_json_list_ is not None:
                if type(response_json_list_) is not list:
                    raise ValueError("reponse_json_list_ needs to be type list")
                j = json.loads(resp_data)
                response_json_list_.append(j)
            return responses[0]
        except BaseException:
            logger.debug("LF post error")
            logger.debug("url: {}".format(self.encode_url(req_url)))
            logger.debug("data: {}".format(data))
            # traceback.print_exc()
            # exit(0)
            return None

    def json_get(self, url):
        """
        Simplified wrapper for GET response as JSON.

        Args:
            url (str): API endpoint.

        Returns:
            dict | None: Parsed JSON response.
        """
        return self.get_as_json(url)

    def json_post(self, url, data, response_json_list_=None):
        """
        Simplified wrapper to POST JSON data.

        Args:
            url (str): API endpoint.
            data (dict): JSON payload.
            response_json_list_ (list|None): Optional list to store response JSON.
        """
        return self.addPostData(url, data, response_json_list_=response_json_list_)

    def wait_until_ports_appear(self, base_url="http://localhost:8080", port_list=(), debug=False, timeout=300):
        """
        Wait until all requested virtual ports become active (non-phantom).

        Args:
            base_url (str): LANforge base URL.
            port_list (list|str): List of port EIDs or single EID.
            debug (bool): Enable debug logs.
            timeout (int): Max wait time in seconds.

        Returns:
            bool: True if all ports appear, False if timeout reached.
        """
        if debug:
            logger.debug("Waiting until ports appear...")
            # existing_stations = LFRequest.LFRequest(base_url, '/ports', debug_=debug)
            existing_stations_url = "/ports"
            # logger.debug('existing ports')
            # logger.debug(pprint.pformat(existing_stations)) # useless
        port_url = "/port/1"
        show_url = "/cli-json/show_ports"
        found_stations = set()
        if base_url.endswith('/'):
            port_url = port_url[1:]
            show_url = show_url[1:]
        if type(port_list) is not list:
            port_list = [port_list]
        if debug:
            # current_ports = LFRequest.LFRequest(base_url, '/ports', debug_=debug).get_as_json()
            current_ports = self.json_get(url="/ports")
            # logger.debug("LFUtils:wait_until_ports_appear, full port listing: %s" % pprint.pformat(current_ports))
            logger.debug("LFUtils:wait_until_ports_appear, full port listing: %s" % current_ports)
            for port in current_ports['interfaces']:
                if list(port.values())[0]['phantom']:
                    logger.debug("LFUtils:waittimeout_until_ports_appear: %s is phantom" % list(port.values())[0]['alias'])
        for attempt in range(0, int(timeout / 2)):
            found_stations = set()
            for port_eid in port_list:
                eid = self.name_to_eid(port_eid)
                shelf = eid[0]
                resource_id = eid[1]
                port_name = eid[2]
                # TODO:  If port_name happens to be a number, especialy '1', then the request below
                # gets a list instead of a single item...and see a few lines down.
                uri = "%s/%s/%s" % (port_url, resource_id, port_name)
                # print("port-eid: %s uri: %s" % (port_eid, uri))
                # lf_r = LFRequest.LFRequest(base_url, uri, debug_=debug)
                # json_response = lf_r.get_as_json()
                json_response = self.json_get(url=uri)
                if json_response is not None:
                    # pprint.pprint(json_response)
                    # TODO:  If a list was (accidentally) requested, this code below will blow up.
                    # This can currently happen if someone manages to name a port 1.1.vap0, ie using
                    # an EID as a name.
                    # TODO:  Fix name_to_eid to somehow detect this and deal with it.
                    if not json_response['interface']['phantom']:
                        found_stations.add("%s.%s.%s" % (shelf, resource_id, port_name))
                else:
                    # lf_r = LFRequest.LFRequest(base_url, show_url, debug_=debug)
                    lf_r_data = {"shelf": shelf, "resource": resource_id, "port": port_name, "probe_flags": 5}
                    # lf_r.jsonPost()
                    self.json_post(url=show_url, data=lf_r_data)
            if len(found_stations) < len(port_list):
                time.sleep(2)
                logger.debug('Found %s out of %s ports in %s out of %s tries in wait_until_ports_appear' % (len(found_stations), len(port_list), attempt, timeout / 2))
            else:
                logger.debug('All %s ports appeared' % len(found_stations))
                return True
        # if debug:
        #     logger.debug("These ports appeared: " + ", ".join(found_stations))
        #     logger.debug("These ports did not appear: " + ",".join(set(port_list) - set(found_stations)))
        #     # logger.debug(pprint.pformat(LFRequest.LFRequest("%s/ports" % base_url)))
        #     logger.debug(LFRequest.LFRequest("%s/ports" % base_url))

        return False

    def name_to_eid(self, eid_input, non_port=False):
        """
        Convert 'shelf.resource.port' style names to EID array format.

        Args:
            eid_input (str): EID string like "1.1.sta0000".
            non_port (bool): Support extended formats (e.g., attenuators).

        Returns:
            list: Parsed EID [shelf, resource, port, extra(optional)].

        Raises:
            ValueError: If format invalid.
        """
        rv = [1, 1, "", ""]
        if (eid_input is None) or (eid_input == ""):
            logger.debug("name_to_eid wants eid like 1.1.sta0 but given[%s]" % eid_input)
            raise ValueError("name_to_eid wants eid like 1.1.sta0 but given[%s]" % eid_input)
        if type(eid_input) is not str:
            logger.debug(
                "name_to_eid wants string formatted like '1.2.name', not a tuple or list or [%s]" % type(eid_input))
            raise ValueError(
                "name_to_eid wants string formatted like '1.2.name', not a tuple or list or [%s]" % type(eid_input))

        info = eid_input.split('.')
        if len(info) == 1:
            rv[2] = info[0]  # just port name
            return rv

        if (len(info) == 2) and info[0].isnumeric() and not info[1].isnumeric():  # resource.port-name
            rv[1] = int(info[0])
            rv[2] = info[1]
            return rv

        elif (len(info) == 2) and not info[0].isnumeric():  # port-name.qvlan
            rv[2] = info[0] + "." + info[1]
            return rv

        if (len(info) == 3) and info[0].isnumeric() and info[1].isnumeric():  # shelf.resource.port-name
            rv[0] = int(info[0])
            rv[1] = int(info[1])
            rv[2] = info[2]
            return rv

        elif (len(info) == 3) and info[0].isnumeric() and not info[1].isnumeric():  # resource.port-name.qvlan
            rv[1] = int(info[0])
            rv[2] = info[1] + "." + info[2]
            return rv

        if non_port:
            # Maybe attenuator or similar shelf.card.atten.index
            rv[0] = int(info[0])
            rv[1] = int(info[1])
            rv[2] = int(info[2])
            if len(info) >= 4:
                rv[3] = int(info[3])
            return rv

        if len(info) == 4:  # shelf.resource.port-name.qvlan
            rv[0] = int(info[0])
            rv[1] = int(info[1])
            rv[2] = info[2] + "." + info[3]

        if len(info) == 5:
            rv[0] = int(info[0])
            rv[1] = int(info[1])
            rv[2] = int(info[2])
            rv[3] = int(info[3])
            # rv[4] = int(info[4])  # need to do more testing for the 5 th element

        return rv

    def admin_up(self, port_eid):
        """
        Bring a LANforge port/admin interface UP.

        Args:
            port_eid (str): EID format, e.g., "1.1.sta0000".
        """
        # print("admin up called")
        # logger.info("186 admin_up port_eid: "+port_eid)
        eid = self.name_to_eid(port_eid)
        resource = eid[1]
        port = eid[2]
        logger.debug("ADMIN UP")
        logger.debug('eid : {}'.format(eid))
        request = self.port_up_request(resource_id=resource, port_name=port)
        logger.debug("request: {}".format(request))
        # logger.info("192.admin_up request: resource: %s port_name %s"%(resource, port))
        dbg_param = ""
        if logger.getEffectiveLevel() == logging.DEBUG:
            # logger.info("enabling url debugging")
            dbg_param = "?__debug=1"
        collected_responses = list()
        self.json_post("/cli-json/set_port%s" % dbg_param, request,
                       response_json_list_=collected_responses)
        # TODO: when doing admin-up ath10k radios, want a LF complaint about a license exception
        # if len(collected_responses) > 0: ...

    def port_up_request(self, resource_id, port_name, debug_on=False):
        """
        Prepare JSON payload for admin-up port request.

        Args:
            resource_id (int): Resource ID.
            port_name (str): Port name.
            debug_on (bool): Enable debug output.

        Returns:
            dict: JSON request body for set_port API.
        """

        if port_name:
            eid = self.name_to_eid(port_name)
            # print('eid inside')
            if resource_id is None:
                resource_id = eid[1]
                port_name = eid[2]
        REPORT_TIMER_MS_FAST = 1500
        data = {
            "shelf": 1,
            "resource": resource_id,
            "port": port_name,
            "current_flags": 0,  # vs 0x1 = interface down
            "interest": 8388610,  # includes use_current_flags + dhcp + dhcp_rls + ifdown
            "report_timer": REPORT_TIMER_MS_FAST,
        }
        if debug_on:
            logger.debug("Port up request")
            logger.debug(debug_printer.pformat(data))
        return data

    def wait_until_cxs_appear(self, these_cx, debug=DEBUG, timeout=100):
        """
        Wait until all requested Layer-3 connections exist.

        Args:
            these_cx (list): Connection names.
            debug (bool): Debug prints.
            timeout (int): Timeout seconds.

        Returns:
            bool: True if all connections exist, False if timeout.
        """
        wait_more = True
        count = 0
        while wait_more:
            wait_more = False
            found_cxs = {}
            cx_list = self.json_get("/cx/list")
            not_cx = ['warnings', 'errors', 'handler', 'uri', 'items']
            if cx_list:
                for cx_name in cx_list:
                    if cx_name in not_cx:
                        continue
                    found_cxs[cx_name] = cx_name

            for req in these_cx:
                if req not in found_cxs:
                    if debug:
                        logger.debug("Waiting on CX: %s" % req)
                    wait_more = True
            count += 1
            if count > timeout:
                if debug:
                    logger.error("ERROR:  Failed to find all cxs: %s" % these_cx)
                return False
            if wait_more:
                time.sleep(1)

        return True

    def sta_clean(self):
        still_looking_sta = True
        iterations_sta = 0
        self_resource = 'all'
        while still_looking_sta and iterations_sta <= 10:
            iterations_sta += 1
            logger.debug(f"sta_clean: iterations_sta: {iterations_sta}")
            try:
                sta_json = self.json_get("/port/?fields=alias")['interfaces']
                # logger.info(sta_json)
            except TypeError:
                # TODO: When would this be the case
                sta_json = None
                logger.warning("sta_json set to None")

            # TODO: Refactor this to make common w/ port removal
            #       And delete on type not on alias
            # get and remove current stations
            if sta_json is not None:
                logger.debug("Removing old stations")
                for name in list(sta_json):
                    for alias in list(name):
                        info = self.name_to_eid(alias)
                        sta_resource = str(info[1])
                        if sta_resource in self_resource or 'all' in self_resource:
                            # logger.info("alias {alias}".format(alias=alias))
                            if 'sta' in alias:
                                info = self.name_to_eid(alias)
                                req_url = "cli-json/rm_vlan"
                                data = {
                                    "shelf": info[0],
                                    "resource": info[1],
                                    "port": info[2]
                                }
                                # logger.info(data)
                                logger.debug(f"Removing {alias}")
                                self.json_post(req_url, data)
                            if 'wlan' in alias:
                                info = self.name_to_eid(alias)
                                req_url = "cli-json/rm_vlan"
                                data = {
                                    "shelf": info[0],
                                    "resource": info[1],
                                    "port": info[2]
                                }
                                # logger.info(data)
                                logger.debug(f"Removing {alias}")
                                self.json_post(req_url, data)

                            # TODO: This isn't a station type port
                            if 'moni' in alias:
                                info = self.name_to_eid(alias)
                                req_url = "cli-json/rm_vlan"
                                data = {
                                    "shelf": info[0],
                                    "resource": info[1],
                                    "port": info[2]
                                }
                                # logger.info(data)
                                logger.debug(f"Removing {alias}")
                                self.json_post(req_url, data)

                            # TODO: Move this to misc cleanup logic
                            if 'Unknown' in alias:
                                info = self.name_to_eid(alias)
                                req_url = "cli-json/rm_vlan"
                                data = {
                                    "shelf": info[0],
                                    "resource": info[1],
                                    "port": info[2]
                                }
                                # logger.info(data)
                                logger.debug(f"Removing {alias}")
                                self.json_post(req_url, data)
                time.sleep(1)
            else:
                logger.info("No further stations found")
                still_looking_sta = False
                logger.debug(f"clean_sta still_looking_sta {still_looking_sta}")

            if not still_looking_sta:
                self.sta_done = True

            return still_looking_sta

    def cxs_clean(self):
        """
        Deletes Layer-3 CXs. Does not remove Layer-3 endpoints.

        See the 'Layer-3' and 'L3 Endps' tabs in the LANforge GUI.
        NOTE: Previously this function removed Layer-3 endpoints as well.
        """
        still_looking_cxs = True
        iterations_cxs = 1

        while still_looking_cxs and iterations_cxs <= 10:
            iterations_cxs += 1
            logger.debug("cxs_clean: iterations_cxs: {iterations_cxs}".format(iterations_cxs=iterations_cxs))
            cx_json = self.json_get("cx")
            # endp_json = super().json_get("endp")
            if cx_json is not None and 'empty' not in cx_json:
                logger.debug(cx_json.keys())
                logger.debug("Removing old cross connects")

                # delete L3-CX based upon the L3-Endp name & the resource value from
                # the e.i.d of the associated L3-Endps
                cx_json.pop("handler")
                cx_json.pop("uri")
                if 'warnings' in cx_json:
                    cx_json.pop("warnings")

                for cx_name in list(cx_json):
                    cxs_eid = cx_json[cx_name]['entity id']
                    cxs_eid_split = cxs_eid.split('.')
                    resource_eid = str(cxs_eid_split[1])
                    # logger.info(resource_eid)

                    if resource_eid in 'all' or 'all' in 'all':
                        # remove Layer-3 cx:
                        req_url = "cli-json/rm_cx"
                        data = {
                            "test_mgr": "default_tm",
                            "cx_name": cx_name
                        }
                        logger.debug(f"Removing {cx_name}")
                        self.json_post(req_url, data)

                time.sleep(5)
            else:
                logger.info("No further Layer-3 CXs found")
                still_looking_cxs = False
                logger.debug(f"clean_cxs still_looking_cxs {still_looking_cxs}")

            if not still_looking_cxs:
                self.cxs_done = True

            return still_looking_cxs

    def layer3_endp_clean(self):
        """
        Delete Layer-3 endpoints with no associated Layer-3 CX.

        To delete a Layer-3 traffic pair in full with this function,
        first cleanup the CX then cleanup its associated Layer-3 endpoints.
        See the 'Layer-3' and 'L3 Endps' tabs in the LANforge GUI.
        """
        still_looking_endp = True
        iterations_endp = 0

        while still_looking_endp and iterations_endp <= 10:
            iterations_endp += 1
            logger.debug("layer3_endp_clean: iterations_endp: {iterations_endp}".format(iterations_endp=iterations_endp))
            endp_json = self.json_get("endp")
            # logger.info(endp_json)
            if endp_json is not None:
                logger.debug("Removing old Layer 3 endpoints")

                # Single endpoint
                if type(endp_json['endpoint']) is dict:
                    endp_name = endp_json['endpoint']['name']
                    req_url = "cli-json/rm_endp"
                    data = {
                        "endp_name": endp_name
                    }
                    # logger.info(data)
                    logger.debug(f"Removing {endp_name}")
                    self.json_post(req_url, data)

                # More than one endpoint
                else:
                    for name in list(endp_json['endpoint']):
                        endp_name = list(name)[0]
                        if name[list(name)[0]]["name"] == '':
                            continue
                        req_url = "cli-json/rm_endp"
                        data = {
                            "endp_name": endp_name
                        }
                        # logger.info(data)
                        logger.debug(f"Removing {endp_name}")
                        self.json_post(req_url, data)
                time.sleep(1)
            else:
                logger.info("No further Layer-3 endpoints found")
                still_looking_endp = False
                logger.debug(f"layer3_clean_endp still_looking_endp {still_looking_endp}")

            if not still_looking_endp:
                self.endp_done = True

            return still_looking_endp

    def pre_cleanup(self):  # cleaning pre-existing stations and cross connections
        self.sta_clean()
        self.cxs_clean()
        self.layer3_endp_clean()

    def wait_until_endps_appear(self, these_endp, debug=DEBUG, timeout=100):
        """
        Wait until LANforge layer3 endpoints are created.

        Args:
            these_endp (list): Endpoint names.
            debug (bool): Enable debug logging.
            timeout (int): Seconds before failing.

        Returns:
            bool: True if endpoints detected, otherwise False.
        """
        wait_more = True
        count = 0
        while wait_more:
            wait_more = False
            endp_list = self.json_get("/endp/list")
            found_endps = {}
            # LAN-2064 the endp_list may be a dict, it shouldbe a list of dictionaries,
            #  need to modify to handle single endpoint as compared to two
            # Realm, wait for endp if there is a single end point it will time out.
            # since json type difference between single station and multiple station
            # logger.debug("endp_list is type {endp}  keys {keys}".format(endp=type(end_list),keys=endp_list.keys()))
            if 'endpoint' in endp_list.keys():
                logger.debug(" endpoint type {}".format(type(endp_list['endpoint'])))
                if not isinstance(endp_list['endpoint'], list):
                    endp_list['endpoint'] = [{endp_list['endpoint']['name']: endp_list['endpoint']}]
                    logger.debug("endp_list {}".format(endp_list))
            if debug:
                logger.debug("Waiting on endpoint endp_list {}".format(endp_list))
            if endp_list and ("items" not in endp_list):
                try:
                    endp_list = list(endp_list['endpoint'])
                    for idx in range(len(endp_list)):
                        name = list(endp_list[idx])[0]
                        found_endps[name] = name
                except BaseException:
                    logger.debug(
                        "non-fatal exception endp_list = list(endp_list['endpoint'] did not exist, will wait some more")
                    print(endp_list)

            for req in these_endp:
                if req not in found_endps:
                    if debug:
                        logger.debug("Waiting on endpoint:{req} count:{count}".format(req=req, count=count))
                    wait_more = True
            count += 1
            if count > timeout:
                logger.error("ERROR:  Could not find all endpoints: %s" % these_endp)
                return False
            if wait_more:
                time.sleep(1)

        return True


class ChamberLain(JSON):
    def __init__(self, mgr, port=8080, side_a_min_rate=0, side_a_max_rate=0,
                 side_b_min_rate=56, side_b_max_rate=0,
                 side_a_min_pdu=-1, side_b_min_pdu=-1, side_a_max_pdu=0, side_b_max_pdu=0,
                 upstream_port="eth1", ssid="", passwd="", security_type="", wifi_pdu=False,
                 wps_username="admin", wps_passwd="1234", wps_ip="192.168.212.152", https=False, transient=False,
                 num_stations=10, radio="wiphy0", client_mac="", wps_outlets="", traffic_type="lf_udp",enable_motion_detection=False):
        super().__init__(lanforge_ip=mgr, port=port)
        self.station_list = []
        self.mgr = mgr
        self.lfclient_url = "http://{}:{}".format(mgr, port)
        self.station_names = []
        self.created_cx = {}
        self.created_endp = {}
        self.side_a_min_bps = side_a_min_rate
        self.side_a_max_bps = side_a_max_rate
        self.side_b_min_bps = side_b_min_rate
        self.side_b_max_bps = side_b_max_rate
        self.side_a_min_pdu = side_a_min_pdu
        self.side_b_min_pdu = side_b_min_pdu
        self.side_a_max_pdu = side_a_max_pdu
        self.side_b_max_pdu = side_b_max_pdu
        self.upstream_port = upstream_port
        self.ssid = ssid
        self.passwd = passwd
        self.security_type = security_type
        self.wifi = wifi_pdu
        self.wps_username = wps_username
        self.wps_passwd = wps_passwd
        self.wps_ip = wps_ip
        self.ping_data = {}
        self.all_ping_data = {}
        self.https = https
        self.transient = transient
        self.num_stations = num_stations
        self.radio = radio
        self.wps_outlets = wps_outlets
        self.client_mac = client_mac
        self.traffic_type = traffic_type
        self.add_sta_flags = ADD_STA_FLAGS
        self.report_data = {}
        self.add_sta_modes = ADD_STA_MODES
        self.set_port_interest_flags = SET_PORT_INTREST_FLAGS
        self.set_port_current_flags = SET_PORT_CURRENT_FLAGS
        self.desired_set_port_current_flags = ["if_down"]
        self.desired_set_port_interest_flags = ["current_flags", "ifdown"]
        self.wifi_extra_data_modified = False
        self.wifi_extra_data = WIFI_EXTRA_DATA
        self.wifi_extra2_data_modified = False
        self.wifi_extra2_data = WIFI_EXTRA2_DATA
        self.wifi_txo_data_modified = False
        self.wifi_txo_data = WIFI_TXO_DATA
        self.rows = []
        self.reset_port_extra_data = RESET_PORT_EXTRA_DATA
        self.csv_names = []
        self.stop_test = False
        self.real_client_ip = ""
        self.failed_ap = []
        self.enable_motion_detection = enable_motion_detection
        self.graph_data = {}
    def station_cleanup():
        pass

    def port_name_series(self, prefix="sta", start_id=0, end_id=1, padding_number=10000, radio=None):
        """
        This produces a named series similar to "sta000, sta001, sta002...sta0(end_id)"
        the padding_number is added to the start and end numbers and the resulting sum
        has the first digit trimmed, so f(0, 1, 10000) => {"0000", "0001"}
        @deprecated -- please use port_name_series
        :param radio:
        :param prefix: defaults to 'sta'
        :param start_id: beginning id
        :param end_id: ending_id
        :param padding_number: used for width of resulting station number
        :return: list of stations
        """

        eid = None
        if radio is not None:
            eid = self.name_to_eid(radio)

        name_list = []
        for i in range((padding_number + start_id), (padding_number + end_id + 1)):
            sta_name = "%s%s" % (prefix, str(i)[1:])
            if eid is None:
                name_list.append(sta_name)
            else:
                name_list.append("%i.%i.%s" % (eid[0], eid[1], sta_name))
        return name_list

    def wait_for_ip(self, station_list=None, ipv4=True, ipv6=False, timeout_sec=300, debug=False):
        # print(station_list)
        logger.info(f"Waiting for IP assignment for : {station_list}")
        # exit(0)
        """
        Wait until IP assigned for created stations.

        Args:
            station_list (list): EIDs of stations.
            ipv4 (bool): Require IPv4.
            ipv6 (bool): Require IPv6.
            timeout_sec (int): Timeout seconds.
            debug (bool): Debug prints.

        Returns:
            bool: True if all stations get IP, False on timeout.
        """
        timeout_auto = False

        if not (ipv4 or ipv6):
            raise ValueError("wait_for_ip: ipv4 and/or ipv6 must be set!")
        if timeout_sec >= 0:
            if debug:
                logger.debug("Waiting for ips, timeout: %i..." % timeout_sec)
        else:
            timeout_sec = 60 + len(station_list) * 5
            if debug:
                logger.debug("Auto-Timeout requested, using: %s" % timeout_sec)

        stas_without_ip4s = {}
        stas_without_ip6s = {}

        sec_elapsed = 0
        start_time = int(time.time())
        # logger.info(station_list)
        waiting_states = ["0.0.0.0", "NA", "", 'DELETED', 'AUTO']
        if (station_list is None) or (len(station_list) < 1):
            logger.critical("wait_for_ip: expects non-empty list of ports")
            raise ValueError("wait_for_ip: expects non-empty list of ports")

        wait_more = True
        while wait_more:
            wait_more = False
            stas_without_ip4s = {}
            stas_without_ip6s = {}

            for sta_eid in station_list:
                eid = self.name_to_eid(sta_eid)

                response = self.json_get("/port/%s/%s/%s?fields=alias,ip,port+type,ipv6+address" %
                                         (eid[0], eid[1], eid[2]))
                # logger.info(pformat(response))

                if (response is None) or ("interface" not in response):
                    logger.debug("station_list: incomplete response for eid: %s:  wait longer" % sta_eid)
                    logger.debug(pformat(response))
                    # print(eid)
                    # exit(0)
                    wait_more = True
                    break

                if ipv4:
                    v = response['interface']
                    if v['ip'] in waiting_states:
                        wait_more = True
                        stas_without_ip4s[sta_eid] = True
                        if debug:
                            logger.debug("Waiting for port %s to get IPv4 Address try %s / %s" % (sta_eid, sec_elapsed, timeout_sec))
                    else:
                        if debug:
                            logger.debug("Found IP: %s on port: %s" % (v['ip'], sta_eid))

                if ipv6:
                    v = response['interface']
                    # logger.info(v)
                    ip6a = v['ipv6_address']
                    if ip6a != 'DELETED' and not ip6a.startswith('fe80') and ip6a != 'AUTO':
                        if debug:
                            logger.debug("Found IPv6: %s on port: %s" % (ip6a, sta_eid))
                    else:
                        stas_without_ip6s[sta_eid] = True
                        wait_more = True
                        if debug:
                            logger.debug("Waiting for port %s to get IPv6 Address try %s / %s, reported: %s." % (sta_eid, sec_elapsed, timeout_sec, ip6a))

            # Check if we need to wait more but timed out. Otherwise, continue polling
            cur_time = int(time.time())
            if wait_more and (cur_time - start_time) > timeout_sec:
                break  # Timed out. Exit while loop
            else:
                sec_elapsed += 1

        # If not all ports got IP addresses before timeout, and debugging is enabled, then
        # add logging.
        if len(stas_without_ip4s) + len(stas_without_ip6s) > 0:
            if debug:
                if len(stas_without_ip4s) > 0:
                    logger.debug('%s did not acquire IPv4 addresses' % stas_without_ip4s.keys())
                if len(stas_without_ip6s) > 0:
                    logger.debug('%s did not acquire IPv6 addresses' % stas_without_ip6s.keys())
                port_info = self.json_get('/port/all')
                logger.debug(pformat(port_info))
            return False
        else:
            if debug:
                logger.debug("Found IPs for all requested ports.")
            return True

    def create_station(self, num_stations, ssid="temp", passwd="temp", security_type="wpa2", radio="wiphy0", mode=MODE_2G, skip_wait_for_ip=False, prefix="sta"):
        """
        Used to virutal WiFi stations and acquire IPs.

        Args:
            num_stations (int): Number of stations.
            ssid (str): WiFi SSID.
            passwd (str): Passphrase.
            security_type (str): open/wpa2/wpa3/owe etc.
            radio (str): LANforge radio interface.
            mode (int): Station mode (default 2.4GHz).

        Raises:
            SystemExit: On failure to acquire IP.
        """
        # mode 2g
        mode = 15
        logger.info(f"Starting station creation: count={num_stations}, ssid={ssid}, radio={radio}")

        # prefix = "sta"
        start_id = 0
        end_id = num_stations  # total-1
        # self.station_list = self.port_name_series(prefix=prefix,start_id=start_id,end_id=end_id-1,radio=radio)
        self.station_list = self.port_name_series(prefix=prefix, start_id=start_id, end_id=end_id - 1, radio=None)
        logger.debug("Stations to create: {}".format(self.station_list))
        self.make_stations_down()
        time.sleep(20)
        # use security
        # self.add_sta_data["ssid"] = ssid
        add_sta_flags = ['wpa2_enable', '80211u_enable', 'create_admin_down']
        add_mask_flags = ['wpa2_enable', '80211u_enable', 'create_admin_down']
        desired_set_port_current_flags = ["if_down"]
        bssid = 'DEFAULT'
        add_sta_data = {
            "shelf": 1,
            "resource": 1,
            "radio": None,
            "sta_name": None,
            "ssid": ssid,
            "key": passwd,
            "mode": 0,
            "mac": "xx:xx:xx:xx:*:xx",
            "flags": 0,  # (0x400 + 0x20000 + 0x1000000000)  # create admin down
            "flags_mask": 0,
            "ap": bssid,
        }
        set_port_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "cmd_flags": 512,
            "current_flags": 2147483648,
            "interest": 16384,  # (0x2 + 0x4000 + 0x800000)  # current, dhcp, down,
        }

        # security part
        SECURITY_TYPES = {
            "open": "[BLANK]",
            "owe": "use-owe",
            "wep": "wep_enable",
            "wpa": "wpa_enable",
            "wpa2": "wpa2_enable",
            "wpa3": "use-wpa3"
        }
        security_type = security_type.lower()
        if security_type in SECURITY_TYPES.keys():
            if (ssid is None) or (ssid == ""):
                raise ValueError("use_security: %s requires ssid" % security_type)
            if (passwd is None) or (passwd == ""):
                raise ValueError("use_security: %s requires passphrase, NA or [BLANK]" % security_type)
            for name in SECURITY_TYPES.values():
                if name in add_sta_flags and name in add_mask_flags:
                    add_sta_flags.remove(name)
                    add_mask_flags.remove(name)
            if security_type != "open":
                add_sta_flags.append(SECURITY_TYPES[security_type])
                # self.set_command_flag("add_sta", types[security_type], 1)
                add_mask_flags.append(SECURITY_TYPES[security_type])
            else:
                passwd = "[BLANK]"
        if security_type == "wpa3":
            add_sta_data["ieee80211w"] = 2
        if security_type == "owe":
            if "80211u_enable" in add_sta_flags:
                add_sta_flags.remove("80211u_enable")
            add_sta_data["ieee80211w"] = 2
            add_sta_flags.append("8021x_radius")
            add_mask_flags.append("8021x_radius")
            add_sta_flags.append("use-owe")
            add_mask_flags.append("use-owe")
        # set command flag
        add_sta_flags.remove("create_admin_down")
        add_mask_flags.append("create_admin_down")
        # sta_names= None,radio=None,up_=False,add_sta_flags=None,add_sta_data=None,add_mask_flags=None,set_port_data=None,sleep_time=0.02,timeout=300
        if not self.create(radio=radio, sta_names=self.station_list, up_=True, add_sta_flags=add_sta_flags, add_sta_data=add_sta_data, add_mask_flags=add_mask_flags, set_port_data=set_port_data):
            logger.info("Station creation FAILED")
        if not skip_wait_for_ip:
            if not self.wait_for_ip(self.station_list):
                logger.info("Stations failed to get IP")
                exit(1)
            else:
                logger.info("all stations got IP")

    def create(self, sta_names=None, radio=None, up_=False, add_sta_flags=None, add_sta_data=None, add_mask_flags=None, set_port_data=None, sleep_time=0.02, timeout=300):
        """
        Core routine to call LANforge APIs and create stations incrementally.

        Handles:
        - add_sta
        - set_port
        - wifi extras
        - waiting for ports to appear
        - admin-up if requested

        Returns:
            bool: True if all stations created successfully.
        """
        starting_event = self.json_get('/events/last/1')['event']['id']
        if not starting_event:
            starting_event = 0
        radio_eid = self.name_to_eid(radio)
        radio_shelf = radio_eid[0]
        radio_resource = radio_eid[1]
        radio_port = radio_eid[2]

        if up_:
            if "create_admin_down" in add_sta_flags:
                del add_sta_flags[add_sta_flags.index("create_admin_down")]
        # else
        add_sta_data["flags"] = self.add_named_flags(add_sta_flags, self.add_sta_flags)
        add_sta_data["flags_mask"] = self.add_named_flags(add_mask_flags, self.add_sta_flags)
        add_sta_data["radio"] = radio_port
        add_sta_data["resource"] = radio_resource
        add_sta_data["shelf"] = radio_shelf
        set_port_data["resource"] = radio_resource
        set_port_data["shelf"] = radio_shelf
        # set_port_data["current_flags"] = self.add_named_flags(self.desired_set_port_current_flags,
        #                                                            self.set_port_current_flags)
        # set_port_data["interest"] = self.add_named_flags(self.desired_set_port_interest_flags,
        #   self.set_port_interest_flags)
        self.wifi_extra_data["resource"] = radio_resource
        self.wifi_extra_data["shelf"] = radio_shelf
        self.wifi_extra2_data["resource"] = radio_resource
        self.wifi_extra2_data["shelf"] = radio_shelf
        self.wifi_txo_data["resource"] = radio_resource
        self.wifi_txo_data["shelf"] = radio_shelf
        self.reset_port_extra_data["resource"] = radio_resource
        self.reset_port_extra_data["shelf"] = radio_shelf
        # add_sta_data[""] = "DEFAULT"
        add_sta_r_url = "/cli-json/add_sta"
        set_port_r_url = "/cli-json/set_port"
        wifi_extra_r_url = "/cli-json/set_wifi_extra"
        wifi_extra2_r_url = "/cli-json/set_wifi_extra2"
        wifi_txo_r_url = "/cli-json/set_wifi_txo"

        my_sta_eids = list()
        for port in sta_names:
            eid = self.name_to_eid(port)
            my_sta_eids.append("%s.%s.%s" % (radio_shelf, radio_resource, eid[2]))
        if (len(my_sta_eids) >= 15):
            add_sta_data["suppress_preexec_cli"] = "yes"
            add_sta_data["suppress_preexec_method"] = 1
            set_port_data["suppress_preexec_cli"] = "yes"
            set_port_data["suppress_preexec_method"] = 1
        num = 0
        finished_sta = []
        skip_create_sta = False
        for eidn in my_sta_eids:
            if eidn in self.station_names:
                logger.info("Station {eidn} already created, skipping.".format(eidn=eidn))
                self.reset_port(eidn)
                time.sleep(20)
                # skip_create_sta = True
                # print("waiting for reset ",eidn)
                # continue
            # if self.debug:
            #     logger.debug(" EIDN " + eidn)
            if eidn in finished_sta:
                # if self.debug:
                #     logger.debug("Station {eidn} already created".format(eidn=eidn))
                continue

            eid = self.name_to_eid(eidn)
            name = eid[2]
            num += 1
            add_sta_data["shelf"] = radio_shelf
            add_sta_data["resource"] = radio_resource
            add_sta_data["radio"] = radio_port
            add_sta_data["sta_name"] = name  # for create station calls
            set_port_data["port"] = name  # for set_port calls.
            set_port_data["shelf"] = radio_shelf
            set_port_data["resource"] = radio_resource

            # add_sta_r_data = add_sta_data
            # if debug:
            #     logger.debug("{date} - 3254 - {eidn}- - - - - - - - - - - - - - - - - - ".format(
            #         date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], eidn=eidn))

            #     logger.debug(pformat(add_sta_r.requested_url))
            #     logger.debug(pformat(add_sta_r.proxies))
            #     logger.debug(pformat(self.add_sta_data))
            #     logger.debug(self.set_port_data)
            #     logger.debug("- ~3254 - - - - - - - - - - - - - - - - - - - ")
            # if dry_run:
            #     if debug:
            #         logger.debug("dry run: not creating {eidn} ".format(eidn=eidn))
            #     continue
            # if debug:
            #     logger.debug('Timestamp: {time_}'.format(time_=(time.time() * 1000)))
            #     logger.debug("- 3264 - ## {eidn} ##  add_sta_r.jsonPost - - - - - - - - - - - - - - - - - - ".format(eidn=eidn))
            # add_sta_r.jsonPost(debug=self.debug)
            if not skip_create_sta:
                logger.debug(f"Sending add_sta for {eidn}")
                self.json_post(url=add_sta_r_url, data=add_sta_data)
                logger.debug(f"set_port applied for station {name}")
            finished_sta.append(eidn)
            # if debug:
            #     logger.debug("- ~3264 - {eidn} - add_sta_r.jsonPost - - - - - - - - - - - - - - - - - - ".format(eidn=eidn))
            time.sleep(0.01)
            total_retries = 30
            current_retries = 1
            created = False
            query = '.'.join([str(radio_shelf), str(radio_resource), str(name)])
            while current_retries <= total_retries:
                logger.debug(f'retrying for {query}')
                logger.debug(f"Waiting for station {query} to appear in port list...")
                # ports_all_data = self.json_get('/ports')
                ports_data = self.json_get("/port/{}/{}/{}?fields=phantom".format(radio_shelf, radio_resource, name))
                logger.debug(ports_data)
                if ports_data is not None and ports_data['interface']['phantom'] == False:
                    created = True
                    break
                time.sleep(1)
            time.sleep(0.01)
            self.json_post(url=set_port_r_url, data=set_port_data)
            # set_port_r.addPostData(self.set_port_data)
            # if debug:
            #     logger.debug("- 3270 -- {eidn} --  set_port_r.jsonPost - - - - - - - - - - - - - - - - - - ".format(eidn=eidn))
            # set_port_r.jsonPost(debug=debug)
            # if debug:
            #     logger.debug("- ~3270 - {eidn} - set_port_r.jsonPost - - - - - - - - - - - - - - - - - - ".format(eidn=eidn))
            time.sleep(0.01)

            self.wifi_extra_data["resource"] = radio_resource
            self.wifi_extra_data["port"] = name
            self.wifi_extra2_data["resource"] = radio_resource
            self.wifi_extra2_data["port"] = name
            self.wifi_txo_data["resource"] = radio_resource
            self.wifi_txo_data["port"] = name
            if self.wifi_extra_data_modified:
                # wifi_extra_r.addPostData(self.wifi_extra_data)
                # wifi_extra_r.jsonPost(debug)
                self.json_post(url=wifi_extra_r_url, data=self.wifi_extra_data)
            if self.wifi_extra2_data_modified:
                # wifi_extra2_r.addPostData(self.wifi_extra2_data)
                # wifi_extra2_r.jsonPost(debug)
                self.json_post(url=wifi_extra2_r_url, data=self.wifi_extra2_data)
            if self.wifi_txo_data_modified:
                # wifi_txo_r.addPostData(self.wifi_txo_data)
                # wifi_txo_r.jsonPost(debug)
                self.json_post(url=wifi_txo_r_url, data=self.wifi_txo_data)

            # append created stations to self.station_names
            self.station_names.append("%s.%s.%s" % (radio_shelf, radio_resource, name))
            time.sleep(sleep_time)

        rv = self.wait_until_ports_appear(self.lfclient_url, my_sta_eids, timeout=timeout)
        if not rv:
            # port creation failed somehow.
            logger.error('ERROR: Failed to create all ports, Desired stations: {my_sta_eids}'.format(my_sta_eids=my_sta_eids))
            logger.error('events')
            logger.error(pformat(self.json_get('/events/since/%s' % starting_event)))
            return False
        if up_:
            # self.admin_up()
            for eid in self.station_names:
                self.admin_up(eid)
        # logger.debug()
        logger.debug("created {num} stations".format(num=num))
        return True

    def add_named_flags(self, desired_list, command_ref):
        """
        Convert flag names into numeric bitmask for LANforge API.

        Args:
            desired_list (list): Flag names.
            command_ref (dict): Flag-to-bit map.

        Returns:
            int: Bitmask int.

        Raises:
            ValueError: On invalid flag name.
        """
        result = 0
        for name in desired_list:
            if (name is None) or (name == ""):
                continue
            if name not in command_ref:
                logger.critical("flag {name} not in map".format(name=name))
                raise ValueError("flag {name} not in map".format(name=name))
            result += command_ref[name]

        return result

    def start_specific(self, cx_list):
        """
        Start layer3 CXs.

        Args:
            cx_list (list): CX names to start.
        """
        # print(cx_list)
        logger.info("Starting L3 CX connections...")

        """
        Starts specific connections from the given list and sets a report timer for them.

        """
        # logging.info("Test started at : {0} ".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        if len(self.created_cx) > 0:
            for cx in cx_list:
                req_url = "cli-json/set_cx_report_timer"
                data = {
                    "test_mgr": "all",
                    "cx_name": cx,
                    "milliseconds": 1000
                }
                self.json_post(req_url, data)
        # logger.info("Starting CXs...")
        for cx_name in cx_list:
            logger.debug(f"Setting CX {cx_name} state to RUNNING")
            # if self.debug:
            #     logger.debug("cx-name: {cx_name}".format(cx_name=cx_name))
            self.json_post("/cli-json/set_cx_state", {
                "test_mgr": "default_tm",
                "cx_name": cx_name,
                "cx_state": "RUNNING"
            })

    def generate_l3_traffic(self, endp_type="TCP", upload_rate="2", download_rate="2", side_a=None, side_b=None, cx_name=None):
        """
        Create LANforge Layer3 CXs and their endpoints(A/B) to generate traffic.

        Args:
            endp_type (str): TCP/UDP/L4 type.
            upload_rate (str): Mbps for uplink.
            download_rate (str): Mbps for downlink.
            side_a (list): List of transmitting stations (EIDs).
            side_b (str): Receiving port (e.g., 'eth1').
            cx_name (str): Base connection name.

        Returns:
            tuple: (list of CX names, list of endpoint names)
        """
        cx_post_data = []
        timer_post_data = []
        these_endp = []
        these_cx = []

        # actual
        side_a_info = self.name_to_eid(side_a[0])
        side_a_shelf = side_a_info[0]
        side_a_resource = side_a_info[1]
        side_b_info = self.name_to_eid(side_b)
        side_b_shelf = side_b_info[0]
        side_b_resource = side_b_info[1]
        endp_a_list, endp_b_list = [], []
        end_point_list = side_a
        self.side_a_min_bps = int(upload_rate) * (10**6)
        self.side_b_min_bps = int(download_rate) * (10**6)

        for port_tuple in end_point_list:
            side_a_info = self.name_to_eid(port_tuple)
            side_a_shelf = side_a_info[0]
            side_a_resource = side_a_info[1]

            endp_a_name = cx_name + "-A"
            endp_b_name = cx_name + "-B"
            self.created_cx[cx_name] = [endp_a_name, endp_b_name]
            self.created_endp[endp_a_name] = endp_a_name
            self.created_endp[endp_b_name] = endp_b_name
            these_cx.append(cx_name)
            these_endp.append(endp_a_name)
            these_endp.append(endp_b_name)
            endp_side_a = {
                "alias": endp_a_name,
                "shelf": side_a_shelf,
                "resource": side_a_resource,
                "port": side_a_info[2],
                "type": endp_type,
                "min_rate": self.side_a_min_bps,
                "max_rate": self.side_a_max_bps,
                "min_pkt": self.side_a_min_pdu,
                "max_pkt": self.side_a_max_pdu,
                "ip_port": -1,
                "multi_conn": 0,
            }
            endp_side_b = {
                "alias": endp_b_name,
                "shelf": side_b_shelf,
                "resource": side_b_resource,
                "port": side_b_info[2],
                "type": endp_type,
                "min_rate": self.side_b_min_bps,
                "max_rate": self.side_b_max_bps,
                "min_pkt": self.side_b_min_pdu,
                "max_pkt": self.side_b_max_pdu,
                "ip_port": -1,
                "multi_conn": 0,
            }

            url = "/cli-json/add_endp"
            logger.debug(f"Creating L3 endpoints for station {port_tuple}")
            self.json_post(url=url,
                           data=endp_side_a,
                           )
            self.json_post(url=url,
                           data=endp_side_b,
                           )
            self.json_post(url="/cli-json/set_endp_report_timer",
                           data={"endp_name": endp_a_name, "milliseconds": 250},
                           )
            self.json_post(url="/cli-json/set_endp_report_timer",
                           data={"endp_name": endp_b_name, "milliseconds": 250, },
                           )
            # time.sleep(sleep_time)

            url = "cli-json/set_endp_flag"
            data = {
                "name": endp_a_name,
                "flag": "AutoHelper",
                "val": 1
            }
            self.json_post(url, data, )
            data["name"] = endp_b_name
            self.json_post(url, data, )

            if (endp_type == "lf_udp") or (endp_type == "udp") or (endp_type == "lf_udp6") or (endp_type == "udp6"):
                data["name"] = endp_a_name
                data["flag"] = "UseAutoNAT"
                self.json_post(url, data)
                data["name"] = endp_b_name
                self.json_post(url, data)

            data = {
                "alias": cx_name,
                "test_mgr": "default_tm",
                "tx_endp": endp_a_name,
                "rx_endp": endp_b_name,
            }
            cx_post_data.append(data)
            timer_post_data.append({
                "test_mgr": "default_tm",
                "cx_name": cx_name,
                "milliseconds": 3000
            })
            cx_name = None
        rv = self.wait_until_endps_appear(these_endp)
        if not rv:
            logger.error("L3CXProfile::create, Could not create/find endpoints")
            return False, False

        for data in cx_post_data:
            url = "/cli-json/add_cx"
            self.json_post(url, data)
            self.json_post("/cli-json/set_cx_report_timer", {"test_mgr": "all", "cx_name": data["alias"], "milliseconds": 8000})
            time.sleep(0.01)

        rv = self.wait_until_cxs_appear(these_cx)
        if not rv:
            logger.error("L3CXProfile::create, Could not create/find connections.")
            return False, these_endp

        return these_cx, these_endp

    def get_wifi_details(self, target_ssid=""):
        self.create_station(num_stations=1, prefix="dummy", skip_wait_for_ip=True)
        # for port in self.sta_list:
        #     port = self.name_to_eid(port)
        #     data = {
        #         "shelf": port[0],
        #         "resource": port[1],
        #         "port": port[2]
        #     }
        #     self.json_post("/cli-json/scan_wifi", data)
        #     print("scanning")
        #     time.sleep(15)
        dummy_station = self.station_list[0]
        logger.info(f"Initiating WiFi scan using dummy station {dummy_station}")
        port = self.name_to_eid(dummy_station)
        data = {
            "shelf": port[0],
            "resource": port[1],
            "port": port[2]
        }
        self.json_post("/cli-json/scan_wifi", data)
        time.sleep(15)
        # scan_results =
        bssid_channel_dict = {}
        scan_results = self.json_get("scanresults/%s/%s/%s" % (port[0], port[1], port[2]))
        # print(scan_results["scan-results"])
        # target_ssid = "NETGEAR_2G_wpa2"
        for item in scan_results["scan-results"]:
            for _, details in item.items():
                print(details)
                if details.get("ssid") == target_ssid:
                    # return details
                    # bssid_channel_dict.append(details)
                    bssid_channel_dict[details['bss']] = details['channel']

        return bssid_channel_dict

    def get_interface_cidrs(self) -> list[ipaddress.IPv4Network]:
        """Extract IPv4 networks from: ip -4 addr show dev eth1"""
        interface = self.upstream_port
        cmd = ["ip", "-4", "addr", "show", "dev", interface]
        result = subprocess.run(cmd, capture_output=True, text=True)

        cidrs = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                # Example: "inet 192.168.4.20/22 brd 192.168.7.255 ..."
                ip_cidr = line.split()[1]  # 192.168.4.20/22
                net = ipaddress.ip_network(ip_cidr, strict=False)
                cidrs.append(net)
        return cidrs

    def get_real_client_ip(self):
        logger.info("Fetching MyQ client ip....")
        # time.sleep(10)
        interface_networks = self.get_interface_cidrs()
        if not interface_networks:
            logger.debug("No IPv4 networks found on interface.")
            return ""
            # exit(1)
        networks_24 = []
        for net in interface_networks:
            networks_24.extend(self.split_into_24s(net))

        # Step 3: run arp-scan on each /24
        for net in networks_24:
            cidr = str(net)
            ip = self.get_ip_by_mac(self.upstream_port, cidr, self.client_mac)
            if ip:
                return ip
        return ""

    def reset_port(self, port):
        eid = self.name_to_eid(port)
        # print("port here",port)
        shelf = eid[0]
        resource_id = eid[1]
        port_name = eid[2]
        port_down_data = self.port_down_request(resource_id, port_name)
        if port.startswith("eth"):
            logger.info(f"Bringing interface {port_name} down.")
        self.json_post(url="cli-json/set_port", data=port_down_data)
        # print("waiting for port down.....")
        time.sleep(20)
        # logger.info(f"Bringing port {port_name} back up...")
        if port.startswith("eth"):
            logger.info(f"Bringing interface {port_name} up.")
        port_up_data = self.port_up_request(resource_id=resource_id, port_name=port_name)
        self.json_post(url="cli-json/set_port", data=port_up_data)

        # reset_port_data = {
        #     "shelf":shelf,
        #     "resource":resource_id,
        #     "port":port_name
        # }
        # self.json_post(url="/cli-json/reset_port",data=reset_port_data)
        # total_retries = 30
        # current_retries = 1
        # created = False
        # query = '.'.join([str(shelf),str(resource_id),str(port_name)])
        # while current_retries <= total_retries:
        #     print(f'retrying for {query}')
        #     # ports_all_data = self.json_get('/ports')
        #     ports_data = self.json_get("/port/{}/{}/{}?fields=phantom".format(shelf,resource_id,port_name))
        #     print(ports_data)
        #     if ports_data is not None and ports_data['interface']['phantom'] == False:
        #         created = True
        #         break
        #     time.sleep(1) YES

    def change_port_to_ip(self, upstream_port):
        if upstream_port.count('.') != 3:
            target_port_list = self.name_to_eid(upstream_port)
            shelf, resource, port, _ = target_port_list
            try:
                target_port_ip = self.json_get(f'/port/{shelf}/{resource}/{port}?fields=ip')['interface']['ip']
                upstream_port = target_port_ip
            except BaseException:
                logging.warning(f'The upstream port is not an ethernet port. Proceeding with the given upstream_port {upstream_port}.')
            logging.debug(f"Upstream port IP {upstream_port}")
        else:
            logging.debug(f"Upstream port IP {upstream_port}")

        return upstream_port

    def get_row_data(self, report_data1, report_data2, switch, i,WPS_CONNECTED_AP_NAMES):
        pass_fail = "PASS" if (report_data1['packet_loss_pass'] & report_data1['latency_pass'] & report_data2['packet_loss_pass'] & report_data2['latency_pass']) else "FAIL"
        no_load_latency = "NA" if report_data1['packet_loss_percent'] == 100.0 else report_data1['average_latency_ms']
        with_load_latency = "NA" if report_data2['packet_loss_percent'] == 100.0 else report_data2['average_latency_ms']
        remarks = ""
        idx =  1
        if not report_data1["packet_loss_pass"]:
            remarks += "{}. {}<br>".format(idx,self.remark_generator(remark="loss",data=report_data1['packet_loss_percent'],load=False))
            idx += 1
        if not report_data2["packet_loss_pass"]:
            remarks += "{}. {}<br>".format(idx,self.remark_generator(remark="loss",data=report_data2['packet_loss_percent'],load=True))
            idx += 1
        if not report_data1["latency_pass"] and no_load_latency!='NA':
            remarks += "{}. {}<br>".format(idx,self.remark_generator(remark="latency",data=report_data1['average_latency_ms'],load=False))
            idx += 1
        if not report_data2["latency_pass"] and with_load_latency!='NA':
            remarks += "{}. {}<br>".format(idx,self.remark_generator(remark="latency",data=report_data2['average_latency_ms'],load=True))
            idx += 1
        # print("here remarks",remarks)
        my_dict = {
            'Sno.': i,
            'Router Model Name': WPS_CONNECTED_AP_NAMES[int(switch)],
            'no_load_connectivity': 'Connected',
            'no_load_avg_ping_loss': report_data1['packet_loss_percent'],
            'no_load_avg_ping_latency': no_load_latency,
            'with_load_connectivity': 'Connected',
            'with_load_avg_ping_loss': report_data2['packet_loss_percent'],
            'with_load_avg_ping_latency': with_load_latency,
            'PASS/FAIL': pass_fail,
            'Remarks' : remarks
        }
        return my_dict

    def simulate_steps(self):
        while True:
            if self.wifi:
                # controller =
                controller = wps.WifiPDU(ROTATOR_WPS_IP, use_https=self.https)
                persistent = True  # transient not supported
            else:
                controller = wps.WebPowerSwitch(ROTATOR_WPS_IP, self.wps_username, self.wps_passwd, use_https=self.https)
                persistent = not self.transient
            logger.debug(f"Turning ON outlet {ROTATOR_WPS_NUMBER}")
            controller.set_outlet(int(ROTATOR_WPS_NUMBER) - 1, True)
            time.sleep(5)
            logger.debug(f"Turning OFF outlet {ROTATOR_WPS_NUMBER}")
            controller.set_outlet(int(ROTATOR_WPS_NUMBER) - 1, False)
            time.sleep(5)

            if self.stop_test:
                return

    def specific_on_off(self,on=False,off=False):
        if self.wifi:
            # controller =
            controller = wps.WifiPDU(ROTATOR_WPS_IP, use_https=self.https)
            persistent = True  # transient not supported
        else:
            controller = wps.WebPowerSwitch(ROTATOR_WPS_IP, self.wps_username, self.wps_passwd, use_https=self.https)
            persistent = not self.transient
        if on:
            logger.debug(f"Turning ON outlet {ROTATOR_WPS_NUMBER}")
            controller.set_outlet(int(ROTATOR_WPS_NUMBER) - 1, True)
        if off:
            logger.debug(f"Turning OFF outlet {ROTATOR_WPS_NUMBER}")
            controller.set_outlet(int(ROTATOR_WPS_NUMBER) - 1, False)




    def fetch_real_client_ip(self):
        real_client_ip = ""
        retries = 1
        total_retries = IP_FETCH_RETRIES
        off = True
        while retries <= total_retries:
            logger.info(f"trying to fetch client ip retry no : {retries}")
            # logger.debug(f"At retry {retries}: Turning ON outlet {ROTATOR_WPS_NUMBER}")
            # self.controller.set_outlet(int(ROTATOR_WPS_NUMBER) - 1, True)
            real_client_ip = self.get_real_client_ip()
            if real_client_ip != "":
                break
            time.sleep(IP_FETCH_INTERVAL)
            # logger.debug(f"At Retry {retries}: Turning OFF outlet {ROTATOR_WPS_NUMBER}")
            # self.controller.set_outlet(int(ROTATOR_WPS_NUMBER) - 1, False)
            retries += 1
        self.real_client_ip = real_client_ip
        self.stop_test = True
    
    # def simulation_led(self,controller):

    #         print(f"Cycle {cycle}: Turning ON outlet {ROTATOR_WPS_NUMBER}")
    #         controller.set_outlet(OUTLET_INDEX, True)

    #         time.sleep(ON_OFF_INTERVAL)

    #         print(f"Cycle {cycle}: Turning OFF outlet {ROTATOR_WPS_NUMBER}")
    #         controller.set_outlet(OUTLET_INDEX, False)

    #         time.sleep(ON_OFF_INTERVAL)


    # def get_ip_and_user_handle(self, action="retry"):
    #     if action == "retry":
    #         user_response = "no"
    #         while user_response.lower() != "yes" and user_response.lower() != "y":
    #             logger.info("Type yes if the MyQ device connection is done:")
    #             try:
    #                 user_response = input().strip().lower()
    #             except (EOFError, ValueError):
    #                 logger.info("Input not available. Assuming 'yes' automatically.")
    #             if user_response != "yes" and user_response != "y":
    #                 logger.info("Give correct input yes/y")
    #         real_client_ip = ""
    #         retries = 1
    #         total_retries = 5
    #         while retries <= total_retries:
    #             logger.info(f"trying to fetch client ip retry no : {retries}")
    #             real_client_ip = self.get_real_client_ip()
    #             if real_client_ip != "":
    #                 break
    #             time.sleep(5)
    #             retries += 1
    #         return real_client_ip
    #     elif action == "exit":
    #         logger.info("Device Failed to get IP")
    #         logger.info("Test stopped by user")
    #         exit(0)

    def make_stations_down(self, station_list=None):
        if station_list is None:
            for station in self.station_list:
                eid = self.name_to_eid(station)
                shelf = eid[0]
                resource_id = eid[1]
                port_name = eid[2]
                port_down_data = self.port_down_request(resource_id=resource_id, port_name=port_name)
                self.json_post(url="cli-json/set_port", data=port_down_data)
        else:
            for station in station_list:
                eid = self.name_to_eid(station)
                shelf = eid[0]
                resource_id = eid[1]
                port_name = eid[2]
                port_down_data = self.port_down_request(resource_id=resource_id, port_name=port_name)
                self.json_post(url="cli-json/set_port", data=port_down_data)

    def turn_off_all_switches(self):
        for idx in range(len(self.wps_ip)):
            logger.info("Turning off all the access points in WPS{}".format(idx+1))
            if self.wifi:
                # controller =
                switch_off = wps.WifiPDU(self.wps_ip[idx], use_https=self.https)
                persistent = True  # transient not supported
            else:
                switch_off = wps.WebPowerSwitch(self.wps_ip[idx], self.wps_username, self.wps_passwd, use_https=self.https)
                persistent = not self.transient
            switch_off.set_all(False, persistent=persistent) if not self.wifi else self.controller.set_all(False)

    def remark_generator(self,remark="",load=False,data=''):
        if remark == "":
            return "No Remarks"
        if remark == "eth":
            return "{} interface Failed to obtain IP Address".format(self.upstream_port)
        if remark == "connectivity":
            return "MyQ device failed to connect to the given SSID {}".format(self.ssid)
        if remark == "loss":
            if load:
                return "with load average ping loss {}% > expected average ping loss {}%".format(data,EXPECTED_PING_LOSS_WITH_LOAD)
            # return "without load "
            return "without load average ping loss {}% > expected  average ping loss {}%".format(data,EXPECTED_PING_LOSS_WITHOUT_LOAD)
        if remark == "latency":
            if load:
                return "with load average ping latency {}ms > expected  average ping latency {}ms".format(data,EXPECTED_PING_LATENCY_WITH_LOAD)
            return "without load average ping latency {}ms > expected  average ping latency {}ms".format(data,EXPECTED_PING_LATENCY_WITHOUT_LOAD)




    def get_temp_row(self,switch,WPS_CONNECTED_AP_NAMES,i,remark=""):
        my_dict = {
            'Sno.': i,
            'Router Model Name': WPS_CONNECTED_AP_NAMES[int(switch)],
            'no_load_connectivity': '-',
            'no_load_avg_ping_loss': '-',
            'no_load_avg_ping_latency': '-',
            'with_load_connectivity': '-',
            'with_load_avg_ping_loss': '-',
            'with_load_avg_ping_latency': '-',
            'PASS/FAIL': '-',
            'Remarks' : self.remark_generator(remark)
        }
        return my_dict      

    def start(self):
        # f
        self.turn_off_all_switches()
        i = 1
        for idx in range(len(self.wps_ip)):
            WPS_CONNECTED_AP_NAMES = WPS_AP_NAMES["WPS{}".format(idx+1)]
            if self.wifi:
                # controller =
                self.controller = wps.WifiPDU(self.wps_ip[idx], use_https=self.https)
                persistent = True  # transient not supported
            else:
                self.controller = wps.WebPowerSwitch(self.wps_ip[idx], self.wps_username, self.wps_passwd, use_https=self.https)
                persistent = not self.transient

            wps_switches = self.wps_outlets[idx]
            # logger.info("Turning off all access points.")
            # self.controller.set_all(False, persistent=persistent) if not self.wifi else self.controller.set_all(False)
            # temp_stations = self.port_name_series(prefix="sta", start_id=0, end_id=NO_OF_STATIONS - 1, radio=None)
            # self.make_stations_down(station_list=temp_stations)
            for switch in wps_switches:
                # on specific switch
                logger.info(f"In WPS{idx+1} Turning ON AP {switch}: {WPS_CONNECTED_AP_NAMES[int(switch)]}")
                time.sleep(5)
                if self.wifi:
                    self.controller.set_outlet(int(switch) - 1, True)
                else:
                    self.controller.set_outlet(int(switch) - 1, True, persistent=True)
                if self.created_cx != {}:
                    self.stop_l3_traffic()
                if self.station_list != []:
                    self.make_stations_down()

                # user_response = "no"
                self.reset_port(self.upstream_port)
                # print("resetting the port")
                time.sleep(10)
                ip_check = self.wait_for_ip(station_list=[self.upstream_port])
                if ip_check:
                    logger.info(f"{self.upstream_port} is up with IP assigned : {self.change_port_to_ip(self.upstream_port)}")
                else:
                    # logger.info(f"Unable to obtain IP address for interface {self.upstream_port}")
                    logger.info(f"Unable to obtain IP address for interface {self.upstream_port}. Waited for 5 minutes, still not obtained. Skipping AP {switch} {WPS_CONNECTED_AP_NAMES[int(switch)]}.")
                    temp_data = self.get_temp_row(switch,WPS_CONNECTED_AP_NAMES,i,remark="eth")
                    self.rows.append(temp_data)
                    i += 1
                    self.failed_ap.append(WPS_CONNECTED_AP_NAMES[int(switch)])
                    if self.wifi:
                        self.controller.set_outlet(int(switch) - 1, False)
                    else:
                        self.controller.set_outlet(int(switch) - 1, False, persistent=persistent)
                    continue
        


                # logger.info("Please connect the MyQ device to the SSID: {}.".format(self.ssid))
                # real_client_ip = self.get_ip_and_user_handle(action="retry")
                # while real_client_ip == "":
                #     logger.info("Enter ‘retry’ to fetch the IP again or ‘exit’ to quit.")
                #     try:
                #         user_response = input().strip().lower()
                #     except (EOFError, ValueError):
                #         logger.info("Input not available. Assuming 'retry' automatically.")
                #         user_response = "retry"
                #     if user_response not in ("retry", "exit"):
                #         logger.info("Invalid input. Enter ‘retry’ to fetch the IP again or ‘exit’ to stop the test.")
                #     else:
                #         real_client_ip = self.get_ip_and_user_handle(action=user_response)
                # get ap's channel optional. (create dummy station and get)
                # ap_data = self.get_wifi_details()
                # if ap_data is None:
                #     logger.error("ap details not found")
                # ap_data =  {'age': '1083', 'auth': 'WPA2', 'beacon': '100', 'bss': '94:a6:7e:74:26:22', 'channel': '11', 'country': 'US', 'entity id': '1.1.wiphy0', 'frequency': '2462', 'info': '2x2 MCS 0-9 AC', 'signal': '-58.0', 'ssid': 'NETGEAR_2G_wpa2'}
                # get device ip
                # cidr = self.get_cidr(interface=self.upstream_port)
                # print("cidr",cidr)
                # real_client_ip = self.get_ip_by_mac(interface=self.upstream_port,cidr=cidr,mac="0c:95:05:96:96:23")
                # print("real_client_ip",real_client_ip)
                # exit(0)
                # if self.make_simulation:
                #     start_time = time.perf_counter()
                #     logger.info("Waiting for the MyQ client to connect...")
                #     self.stop_test = False
                #     # self.simulate_steps(True)
                #     # self.fetch_real_client_ip()
                #     # self.simulate_steps(False)
                #     # real_client_ip =self.fetch_real_client_ip()
                #     t1 = threading.Thread(target=self.fetch_real_client_ip)
                #     t2 = threading.Thread(target=self.simulate_steps)
                #     t1.start()
                #     t2.start()
                    

                #     t1.join()
                #     self.stop_test = True
                #     t2.join()

                #     real_client_ip = self.real_client_ip
                #     end_time = time.perf_counter()
                #     elapsed_seconds = end_time - start_time
                #     elapsed_minutes = elapsed_seconds // 60
                #     elapsed_seconds_only = int(elapsed_seconds % 60)
                # else:
                if self.enable_motion_detection:
                    self.specific_on_off(on=True)
                start_time = time.perf_counter()
                logger.info("Waiting for the MyQ client to connect...")
                self.fetch_real_client_ip()
                real_client_ip = self.real_client_ip
                end_time = time.perf_counter()
                elapsed_seconds = end_time - start_time
                elapsed_minutes = elapsed_seconds // 60
                elapsed_seconds_only = int(elapsed_seconds % 60)


                if real_client_ip == "":
                    logger.info(f"Unable to obtain IP address for MyQ Device . Waited for {IP_FETCH_RETRIES} Retries and {elapsed_minutes} minutes, still not obtained. Skipping AP {switch} {WPS_CONNECTED_AP_NAMES[int(switch)]}.")
                    # temp_data = self.get_temp_row()
                    temp_data = self.get_temp_row(switch,WPS_CONNECTED_AP_NAMES,i,remark="connectivity")
                    self.rows.append(temp_data)

                    i += 1
                    if self.enable_motion_detection:
                        self.specific_on_off(off=True)
                    self.failed_ap.append(WPS_CONNECTED_AP_NAMES[int(switch)])
                    if self.wifi:
                        self.controller.set_outlet(int(switch) - 1, False)
                    else:
                        self.controller.set_outlet(int(switch) - 1, False, persistent=persistent)
                    continue
                
                # logger.info(f"MyQ Client took {elapsed_minutes} minutes to connect after bringing up {self.upstream_port}.")
                minutes_text = f"{elapsed_minutes} minutes and " if elapsed_minutes else ""
                logger.info(f"MyQ client took {minutes_text} {elapsed_seconds_only} seconds to connect after bringing up {self.upstream_port}.")
                logger.info(f"MyQ device IP : {real_client_ip}.")


                
                # self.simulation_led(controller)
                ping_data = self.ping_for_duration(real_client_ip, PING_TIME / 2, "{}_NOLOAD_{}".format(WPS_CONNECTED_AP_NAMES[int(switch)],switch),load=False)
                logger.info("PING DATA WITHOUT LOAD")
                print(ping_data)
                report_data1 = self.get_report_dict(df=ping_data, load=False)
                # print('report data 1',report_data1)
                logger.info("Aggregated Ping data without load {}".format(report_data1))
                # get average latency
                self.create_station_and_run_traffic()
                ping_data = self.ping_for_duration(real_client_ip, PING_TIME / 2,"{}_WITHLOAD_{}".format(WPS_CONNECTED_AP_NAMES[int(switch)],switch) ,load=True)
                logger.info("PING DATA WITH LOAD")
                print(ping_data)
                report_data2 = self.get_report_dict(df=ping_data, load=True)
                ap_name = WPS_CONNECTED_AP_NAMES[int(switch)]
                if WPS_CONNECTED_AP_NAMES[int(switch)] not in self.graph_data:
                    self.graph_data[ap_name] = {}
                self.graph_data[ap_name]['latency'] = report_data1['average_latency_ms']
                self.graph_data[ap_name]['load_latency'] = report_data2['average_latency_ms']
                # print('report data2',report_data2)
                logger.info("Aggregated Ping data with load {}".format(report_data2))
                row_data = self.get_row_data(report_data1, report_data2, switch, i,WPS_CONNECTED_AP_NAMES)
                self.rows.append(row_data)
                # self.all_ping_data[switch] = self.ping_data.copy()
                # self.ping_data = {}
                if self.wifi:
                    self.controller.set_outlet(int(switch) - 1, False)
                else:
                    self.controller.set_outlet(int(switch) - 1, False, persistent=persistent)
                logger.info(f"In WPS{idx+1} Turning OFF AP {switch} : {WPS_CONNECTED_AP_NAMES[int(switch)]}")
                i += 1
                if self.enable_motion_detection:
                    self.specific_on_off(off=True)


    def stop_l3_cx(self, cx_name):
        self.json_post("/cli-json/set_cx_state", {
            "test_mgr": "ALL",
            "cx_name": cx_name,
            "cx_state": "STOPPED"
        })

    def stop_l3_traffic(self):
        logger.info("Stopping Layer3 cx's")
        for cx_name in self.created_cx.keys():
            self.stop_l3_cx(cx_name)

    def create_station_and_run_traffic(self):
        if self.station_list == []:
            self.create_station(num_stations=self.num_stations, ssid=self.ssid, passwd=self.passwd, security_type=self.security_type, radio=self.radio)
        else:
            logger.info(f"Bringing stations up {self.station_list}")
            for station in self.station_list:
                eid = self.name_to_eid(station)
                shelf = eid[0]
                resource_id = eid[1]
                port_name = eid[2]
                # port_up_data =
                port_up_data = self.port_up_request(resource_id=resource_id, port_name=port_name)
                self.json_post(url="cli-json/set_port", data=port_up_data)
            if not self.wait_for_ip(self.station_list):
                print("Stations failed to get IP")
                exit(1)
            else:
                print("all stations got IP")

        # self.generate_l3_traffic()
        port_lists = []
        eid_list = []
        # print(self.station_list)
        for i in self.station_list:
            # print(self.name_to_eid(i))
            eid = self.name_to_eid(i)
            eid_list.append(eid)
            port_lists.append('.'.join(str(x) for x in eid if x))
        # print(port_lists)
        # print(eid_list)
        count = 0
        traffic_type = self.traffic_type
        # logger.info("Creatstop_l3_trafficing connections for endpoint type: %s cx-count: %s" % (
        logger.info(f"Generating L3 traffic: type={traffic_type}, upload={UPLOAD_RATE}Mbps, download={DOWNLOAD_RATE}Mbps")
        if self.created_cx == {}:
            for station in range(len(port_lists)):
                logger.debug("Creating connections for endpoint type: %s cx-count: %s" % (
                    traffic_type, count))
                self.generate_l3_traffic(endp_type=traffic_type, side_a=[port_lists[station]],
                                         side_b="eth1", cx_name="%s" % (self.station_list[count]), upload_rate=UPLOAD_RATE, download_rate=DOWNLOAD_RATE)
                count += 1

        self.start_specific(self.created_cx)

    def extract_icmp_line(self, output):
        """Return only the ICMP response line."""
        for line in output.split("\n"):
            if "time=" in line.lower() or "ttl=" in line.lower():
                return line.strip()
            if "timeout" in line.lower():
                return line.strip()
        return output.strip()  # fallback

    def parse_ping_line(self, line):
        """Parse a cleaned ICMP line."""
        result = {
            "status": "timeout",
            "latency_ms": None,
            "packet_loss": 1,
            "raw": line.strip()
        }

        if "time=" in line.lower():  # Success
            result["status"] = "success"
            result["packet_loss"] = 0

            match = re.search(r'time[=<]\s*([\d\.]+)\s*ms', line)
            if match:
                result["latency_ms"] = float(match.group(1))

        return result

    def get_cidr(self, interface):
        try:
            result = subprocess.run(
                ["ip", "-o", "-f", "inet", "addr", "show", interface],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                for part in parts:
                    if "/" in part:
                        return part  # example: 192.168.4.10/24
        except Exception as e:
            print("Error:", e)
        return None

    def split_into_24s(self, network: ipaddress.IPv4Network) -> list[ipaddress.IPv4Network]:
        """Break any CIDR (e.g., /22) into /24 blocks."""
        if network.prefixlen <= 24:
            return list(network.subnets(new_prefix=24))
        else:
            # If someone uses a /25 or smaller range
            return [network]

    def get_ip_by_mac(self, interface: str, cidr: str, mac: str, timeout: int = 20) -> str | None:
        target_mac = mac.lower()
        cmd = ["sudo", "arp-scan", "-I", interface, cidr]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None

        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                ip, found_mac = parts[0], parts[1].lower()
                if found_mac == target_mac:
                    return ip

        return None

    def ping_for_duration(self, ip, duration, switch, load=False):
        # is_windows = platform.system().lower() == "windows"
        # ping_cmd = ["ping", "-n", "1", ip] if is_windows else ["ping", "-c", "1", ip]
        # ping_cmd = ["ping", "-c", "1", "-W", "1", ip]  # 1-second timeout
        ping_cmd = ["ping", "-I", self.upstream_port, "-c", "1", "-W", "1", ip]

        data = []
        seq = 1
        end = time.time() + duration
        # print("estimated end time",end)
        if load:
            load_txt = "with load"
        else:
            load_txt = "without load"
        logger.info(f"Initiating {duration/60}-minute ping test to {ip} {load_txt}")
        
        while time.time() < end:
            # print("pinging")
            # print(f"icmp_seq={seq} time={parsed.get('latency_ms', 'timeout')} ms")
            timestamp = datetime.datetime.now()

            proc = subprocess.run(ping_cmd, capture_output=True, text=True)
            icmp_line = self.extract_icmp_line(proc.stdout + proc.stderr)
            parsed = self.parse_ping_line(icmp_line)

            parsed["timestamp"] = timestamp
            parsed["seq"] = seq
            parsed["ip"] = ip
            # print(f"icmp_seq={seq} time={parsed.get('latency_ms', 'timeout')} ms")
            data.append(parsed)

            seq += 1
            time.sleep(1)
        df = pd.DataFrame(data)
        df.to_csv('{}.csv'.format(switch), index=False)
        self.csv_names.append('{}.csv'.format(switch))
        # self.ping_data = pd.DataFrame(data)
        return df

    def get_report_dict(self, df, load=False):
        """
        Analyze ping test results from a DataFrame.

        Parameters:
            df (pd.DataFrame): Must contain 'latency_ms' and 'packet_loss' columns.
            max_loss_percent (float): Allowed maximum packet loss percentage.
            max_latency_ms (float): Allowed maximum average latency in ms.

        Returns:
            dict: {
                'packet_loss_percent': float,
                'average_latency_ms': float,
                'packet_loss_pass': bool,
                'latency_pass': bool
            }
        """
        if 'packet_loss' not in df.columns or 'latency_ms' not in df.columns:
            raise ValueError("DataFrame must contain 'packet_loss' and 'latency_ms' columns")
        max_loss_percent = EXPECTED_PING_LOSS_WITH_LOAD if load else EXPECTED_PING_LOSS_WITHOUT_LOAD
        max_latency_ms = EXPECTED_PING_LATENCY_WITH_LOAD if load else EXPECTED_PING_LATENCY_WITHOUT_LOAD
        total_pings = len(df)
        lost_packets = df['packet_loss'].sum()
        packet_loss_percent = (lost_packets / total_pings) * 100 if total_pings > 0 else 0.0

        successful_pings = df[df['packet_loss'] == 0]
        average_latency_ms = successful_pings['latency_ms'].mean() if not successful_pings.empty else 0.0

        packet_loss_pass = packet_loss_percent <= max_loss_percent
        latency_pass = average_latency_ms <= max_latency_ms

        # Convert NumPy types to native Python types
        return {
            'packet_loss_percent': float(round(packet_loss_percent, 2)),
            'average_latency_ms': float(round(average_latency_ms, 2)),
            'packet_loss_pass': bool(packet_loss_pass),
            'latency_pass': bool(latency_pass)
        }

    def get_test_setup_info(self):
        test_ap = []
        test_setup_info = {}
        for idx in range(len(self.wps_ip)):
            wps_ap_names = WPS_AP_NAMES["WPS{}".format(idx+1)]
            wps_switches = self.wps_outlets[idx]
            for switch in wps_switches:
                test_ap.append(wps_ap_names[int(switch)])
        test_setup_info["DUT"] = DUT_NAME
        test_setup_info["SSID"] = self.ssid
        test_setup_info["Security"] = self.security_type
        test_setup_info["APs Included in test"] = ','.join(test_ap)
        test_setup_info["Test duration per AP (min)"] = round(PING_TIME/60,2)

        return test_setup_info


    # def create_double_line_graph(self):
    #     data = self.graph_data
    #     aps = list(data.keys())
    #     latencies = [data[ap]["latency"] for ap in aps]
    #     load_latencies = [data[ap]["load_latency"] for ap in aps]
    #     plt.figure(figsize=(13, 6))

    #     # Plot latency
    #     plt.plot(
    #         aps, latencies,
    #         marker="o", linewidth=2,
    #         label="Avg. Baseline Latency (ms)"
    #     )

    #     # Plot load latency
    #     plt.plot(
    #         aps, load_latencies,
    #         marker="s", linewidth=2,
    #         label="Avg. Load Latency (ms)"
    #     )
    #     # for x, y in zip(aps, latencies):
    #     #     plt.text(x, y, str(y), ha='center', va='bottom', fontsize=9)

    #     # for x, y in zip(aps, load_latencies):
    #     #     plt.text(x, y, str(y), ha='center', va='bottom', fontsize=9)

    #     # Add value labels with good separation
    #     # for x, y in zip(aps, latencies):
    #     #     plt.text(x, y + 10, str(y), ha='center', va='bottom', fontsize=9)

    #     # for x, y in zip(aps, load_latencies):
    #     #     plt.text(x, y + 10, str(y), ha='center', va='bottom', fontsize=9)

    #     for x, y in zip(aps, latencies):
    #         plt.text(x, y + 25, str(y), ha='center', va='bottom', fontsize=9)

    #     for x, y in zip(aps, load_latencies):
    #         plt.text(x, y - 25, str(y), ha='center', va='top', fontsize=9)



    #     # plt.title("Ping Latency Behavior of APs Under Idle and Load Conditions")
    #     plt.title("Ping Latency Behavior of APs Under Idle and Load Conditions")
    #     plt.xlabel("Access Points")
    #     plt.ylabel("Latency(ms)")
    #     # plt.grid()
    #     plt.legend()

    #     # Rotate AP names for readability
    #     plt.xticks(rotation=45, ha='right')

    #     plt.tight_layout()
    #     graph_image_name = "latency_plot.png"
    #     # Save image
    #     plt.savefig(graph_image_name, dpi=300)

    #     # print("Image saved as latency_plot.png")
    #     return graph_image_name

    def create_double_line_graph(self):
        import textwrap

        data = self.graph_data
        aps = list(data.keys())
        # Add line breaks to long AP names (wrap at 15 characters)
        aps_wrapped = ['\n'.join(textwrap.wrap(ap, 15)) for ap in aps]

        latencies = [data[ap]["latency"] for ap in aps]
        load_latencies = [data[ap]["load_latency"] for ap in aps]

        plt.figure(figsize=(15, 8))

        # Scatter baseline latency
        plt.scatter(
            aps_wrapped, latencies,
            marker="o", linewidth=2,
            label="Avg. Baseline Latency (ms)"
        )

        # Scatter load latency
        plt.scatter(
            aps_wrapped, load_latencies,
            marker="s", linewidth=2,
            label="Avg. Load Latency (ms)"
        )

        # Value labels (top for baseline)
        for x, y in zip(aps_wrapped, latencies):
            if y != 0.0:
                plt.text(
                    x, y + 3, str(y),
                    ha='center', va='bottom', fontsize=9
                )

        # Value labels (bottom for load)
        for x, y in zip(aps_wrapped, load_latencies):
            if y != 0.0:
                plt.text(
                    x, y - 3, str(y),
                    ha='center', va='top', fontsize=9
                )

        # Ensure labels stay inside
        all_values = latencies + load_latencies
        plt.ylim(0, max(all_values) + 40)

        # Title & labels
        plt.title("Ping Latency Behavior of APs Under Idle and Load Conditions")
        plt.xlabel("Access Points")
        plt.ylabel("Latency (ms)")
        plt.legend()

        # Rotate x-axis labels to 180°
        plt.xticks(rotation=360)

        # Prevent overlapping when many APs exist
        plt.tight_layout()

        # Save image
        graph_image_name = "latency_plot.png"
        plt.savefig(graph_image_name, dpi=300)

        return graph_image_name


    def generate_report(self):
        rows = self.rows.copy()
        header_rows = [
            [   # first header row: Sno., Router Model Name, 3-col group, 3-col group, Remarks
                {'label': 'Sno.', 'rowspan': 2},
                {'label': 'Router Model Name', 'rowspan': 2},
                {'label': 'Without additional STAs (Without Load)', 'colspan': 3},
                {'label': 'With additional STAs (With Load)', 'colspan': 3},
                {'label': 'PASS/FAIL', 'rowspan': 2},
                {'label': 'Remarks', 'rowspan': 2},

            ],
            [   # second header row: sub-headers for the two 3-col groups
                {'label': 'Client connectivity<br>throughout the test'},
                {'label': 'Avg. ping loss (%)'},
                {'label': 'Avg Ping latency(ms)'},
                {'label': 'Client connectivity<br>throughout the test'},
                {'label': 'Avg. ping loss (%)'},
                {'label': 'Avg Ping latency(ms)'}
            ]
        ]
        column_keys = [
            'Sno.',
            'Router Model Name',
            'no_load_connectivity',
            'no_load_avg_ping_loss',
            'no_load_avg_ping_latency',
            'with_load_connectivity',
            'with_load_avg_ping_loss',
            'with_load_avg_ping_latency',
            'PASS/FAIL',
            'Remarks'
        ]
        report = lf_report.lf_report(_results_dir_name="load_handling_test", _output_html="load_handling_test.html", _output_pdf="load_handling_test.pdf", _path='')
        report_path_date_time = report.get_path_date_time()
        for csv_name in self.csv_names:
            shutil.move(csv_name, report_path_date_time)
        report.set_title("ROUTER COMPATIBILITY TEST")
        # date = """{} <br>
        #         Load Handling""".format(date)
        date = str(datetime.datetime.now()).split(",")[0].replace(" ", "-").split(".")[0]
        date_new = """Load Handling <br> <br> <br> <br> <br> {}""".format(date)
        report.set_date(date_new)
        report.build_banner()
        report.set_table_title("Test Setup Information")
        report.build_table_title()
        test_setup_info = self.get_test_setup_info()
        report.test_setup_table(value="Test Setup Information", test_setup_data=test_setup_info)
        report.set_obj_html("Objective",
                            "The objective of this test is to verify the Chamberlain DUT's connectivity "
                            "across various routers and assess the impact of load on the DUT's performance. "
                            "This test compares the average ping loss and average ping latency of the DUT"
                            "with and without additional load on the router to analyse the impact of load.")
        
        report.build_objective()
        report.set_obj_html("Procedure",
                            "1. Turn on Router 1(R1).<br>"
                            "2. Configure the CHAMBERLAIN DEVICE(DUT) and connect it to the test SSID.<br>"
                            f"3. Start running <b> PING </b> from the R1 upstream to DUT for a total duration of <b>{round(PING_TIME/60,2)} minutes</b>.<br>"
                            f"4. After {round((PING_TIME/60)/2,2)} minutes, stop the ping session. Create and connect <b>{NO_OF_STATIONS} virtual clients</b> to the same router.<br>"
                            f"5. Run TCP uplink and downlink traffic at {UPLOAD_RATE} Mbps per direction per client until the remaining 5-minute ping session is finished.<br>"
                            f"6. At the end of the second {round((PING_TIME/60)/2,2)}-minute session, disconnect all virtual clients and turn off R1.<br>"
                            "7. Turn on R2 and repeat the above steps from 2-6.<br>"
                            "8. Continue the same procedure sequentially for all remaining routers (R3 to R10).<br><br>")
        report.build_objective()
        report.set_obj_html(
            _obj_title=f"Ping latency with and without load",
            _obj="The graph below illustrates the average ping latency observed for the Device Under Test (DUT) across various routers, "
                "comparing measurements recorded in both no-load and with load conditions.")
        report.build_objective()
        graph_png = self.create_double_line_graph()
        report.set_graph_image(graph_png)
        report.move_graph_image()
        report.build_graph()
        report.set_obj_html("Test Observations","")
        report.build_objective()
        table = report.generate_html_table(header_rows, column_keys, rows)
        report.html += table

        report.set_obj_html("Note:",
                            "The P/F criteria for the test are as follows:<br>"
                            "1. The DUT should maintain connectivity in both cases (with and without load).<br>"
                            f"2. The average ping loss without load should be less than or equal to {EXPECTED_PING_LOSS_WITHOUT_LOAD}%.<br>"
                            f"3. The average ping loss with load should be less than or equal to {EXPECTED_PING_LOSS_WITH_LOAD}%.<br>"
                            f"4. The average ping latency without load should be less than or equal to {EXPECTED_PING_LATENCY_WITHOUT_LOAD}ms.<br>"
                            f"5. The average ping loss with load should be less than or equal to {EXPECTED_PING_LATENCY_WITH_LOAD}ms.<br><br>"
                            "All the above criteria should be met for the test to be considered as PASS.<br>")
        report.build_objective()
        report.build_footer()
        html_file = report.write_html()
        logger.info("returned file {}".format(html_file))
        logger.info(html_file)
        report.write_pdf()


def validate_config():
    errors = []

    # 1. DUT_NAME
    if not isinstance(DUT_NAME, str) or not DUT_NAME.strip():
        errors.append("DUT_NAME must be a non-empty string.")

    # 2. MGR
    if not isinstance(MGR, str) or not MGR.strip():
        errors.append("MGR must be a non-empty string.")

    # 3. PORT
    if isinstance(PORT, int):
        if PORT <= 0:
            errors.append("PORT must be a positive integer.")
    elif isinstance(PORT, str):
        if not PORT.isdigit() or int(PORT) <= 0:
            errors.append("PORT must be a positive numeric string.")
    else:
        errors.append("PORT must be either int or a numeric string.")

    # 4. SSID / PASSWORD / SECURITY
    if not isinstance(SSID, str) or not SSID.strip():
        errors.append("SSID must be a non-empty string.")

    if not isinstance(PASSWORD, str):
        errors.append("PASSWORD must be a string.")

    if SECURITY not in ["wpa2", "wpa3", "open"]:
        errors.append("SECURITY must be one of: 'wpa2', 'wpa3', 'open'.")

    # 5. NO_OF_STATIONS
    if not isinstance(NO_OF_STATIONS, int) or NO_OF_STATIONS <= 0:
        errors.append("NO_OF_STATIONS must be a positive integer.")

    # 6. WIPHY_RADIO
    if not isinstance(WIPHY_RADIO, str) or not WIPHY_RADIO.strip():
        errors.append("WIPHY_RADIO must be a non-empty string.")

    # 7. UPSTREAM_PORT
    if not isinstance(UPSTREAM_PORT, str) or not UPSTREAM_PORT.strip():
        errors.append("UPSTREAM_PORT must be a non-empty string.")

    # 8. TRAFFIC_TYPE
    if TRAFFIC_TYPE not in ["tcp", "udp"]:
        errors.append("TRAFFIC_TYPE must be either 'tcp' or 'udp'.")

    # 9. UPLOAD_RATE / DOWNLOAD_RATE
    for var_name, var_value in [("UPLOAD_RATE", UPLOAD_RATE), ("DOWNLOAD_RATE", DOWNLOAD_RATE)]:
        if isinstance(var_value, int):
            if var_value <= 0:
                errors.append(f"{var_name} must be > 0.")
        elif isinstance(var_value, str):
            if not var_value.isdigit() or int(var_value) <= 0:
                errors.append(f"{var_name} must be a positive number (int or numeric string).")
        else:
            errors.append(f"{var_name} must be int or numeric string.")

    # 10. WPS_IP
    if not isinstance(WPS_IP, list) or not WPS_IP:
        errors.append("WPS_IP must be a non-empty list of IP strings.")
    else:
        for ip in WPS_IP:
            if not isinstance(ip, str) or not ip.strip():
                errors.append("Each item in WPS_IP must be a non-empty IP string.")
                break

    # 11. WPS_USERNAME / WPS_PASSWORD
    if not isinstance(WPS_USERNAME, str) or not WPS_USERNAME.strip():
        errors.append("WPS_USERNAME must be non-empty.")
    if not isinstance(WPS_PASSWORD, str) or not WPS_PASSWORD.strip():
        errors.append("WPS_PASSWORD must be non-empty.")

    # 12. WPS_OUTLETS
    if not isinstance(WPS_OUTLETS, list) or not WPS_OUTLETS:
        errors.append("WPS_OUTLETS must be a non-empty list of lists.")
    else:
        for lst in WPS_OUTLETS:
            if not isinstance(lst, list):
                errors.append("WPS_OUTLETS must be a list of lists.")
                break
            for outlet in lst:
                if not isinstance(outlet, str) or not outlet.isdigit() or int(outlet) <= 0:
                    errors.append("All outlet numbers in WPS_OUTLETS must be positive digit strings.")
                    break

    # 13. WPS_AP_NAMES
    if not isinstance(WPS_AP_NAMES, dict) or not WPS_AP_NAMES:
        errors.append("WPS_AP_NAMES must be a non-empty dictionary.")
    else:
        for wps_key, ap_dict in WPS_AP_NAMES.items():
            if not isinstance(wps_key, str):
                errors.append("Keys in WPS_AP_NAMES must be strings.")
                break
            if not isinstance(ap_dict, dict):
                errors.append(f"{wps_key} in WPS_AP_NAMES must map to a dictionary.")
                break
            for outlet_no, ap_name in ap_dict.items():
                if not isinstance(outlet_no, int) or outlet_no <= 0:
                    errors.append(f"Outlet index {outlet_no} in {wps_key} must be positive integer.")
                if not isinstance(ap_name, str) or not ap_name.strip():
                    errors.append(f"AP name for outlet {outlet_no} in {wps_key} must be a non-empty string.")

    # 14. PING_TIME
    if not isinstance(PING_TIME, int) or PING_TIME <= 0:
        errors.append("PING_TIME must be a positive integer.")

    # 15. EXPECTED LOSS
    if not isinstance(EXPECTED_PING_LOSS_WITHOUT_LOAD, (int, float)):
        errors.append("EXPECTED_PING_LOSS_WITHOUT_LOAD must be numeric.")
    if not isinstance(EXPECTED_PING_LOSS_WITH_LOAD, (int, float)):
        errors.append("EXPECTED_PING_LOSS_WITH_LOAD must be numeric.")

    # 16. Ping latency
    if not isinstance(EXPECTED_PING_LATENCY_WITHOUT_LOAD, int):
        errors.append("EXPECTED_PING_LATENCY_WITHOUT_LOAD must be integer.")
    if not isinstance(EXPECTED_PING_LATENCY_WITH_LOAD, int):
        errors.append("EXPECTED_PING_LATENCY_WITH_LOAD must be integer.")

    # 17 & 18. IP fetch params
    if not isinstance(IP_FETCH_INTERVAL, int) or IP_FETCH_INTERVAL <= 0:
        errors.append("IP_FETCH_INTERVAL must be a positive integer.")

    if not isinstance(IP_FETCH_RETRIES, int) or IP_FETCH_RETRIES <= 0:
        errors.append("IP_FETCH_RETRIES must be a positive integer.")

    # 19. ROTATOR_WPS_NUMBER
    if not isinstance(ROTATOR_WPS_NUMBER, int) or ROTATOR_WPS_NUMBER <= 0:
        errors.append("ROTATOR_WPS_NUMBER must be a positive integer.")

    # 20. ROTATOR_WPS_IP
    if not isinstance(ROTATOR_WPS_IP, str) or not ROTATOR_WPS_IP.strip():
        errors.append("ROTATOR_WPS_IP must be a non-empty string.")

    # Final check
    if errors:
        print("\n".join(errors))
        exit(1)

def main():
    import argparse
    validate_config()
    traffic_type = "lf_{}".format(TRAFFIC_TYPE.lower())

    parser = argparse.ArgumentParser(
        description="Load Balancing"
    )
    parser.add_argument("--mgr", help="LANforge Manager IP", default=MGR)
    parser.add_argument("--port", type=int, default=PORT, help="LANforge HTTP port (default: 8080)")

    parser.add_argument("--ssid", help="SSID of the WiFi network", default=SSID)
    parser.add_argument("--passwd", help="WiFi password", default=PASSWORD)
    parser.add_argument(
        "--security", choices=["open", "wep", "wpa", "wpa2", "wpa3", "owe"],
        default=SECURITY, help="Wi-Fi security mode"
    )
    parser.add_argument("--num_stations", type=int, default=NO_OF_STATIONS, help="Number of stations to create (default: 10)")
    parser.add_argument("--radio", default="wiphy0", help="Radio interface, e.g. wiphy0, wiphy1 (default: wiphy0)")
    parser.add_argument(
        "--upstream_port", "-u", default="eth1",
        help="Non-station port that generates traffic: <resource>.<port>, e.g: 1.eth1 (default: eth1)"
    )

    # Back-compat shorthands (kept): map to min-rate if explicit rates not provided
    parser.add_argument("--upload", help="Legacy: upload rate Mbps (maps to side-a-min-rate)", default=UPLOAD_RATE)
    parser.add_argument("--download", help="Legacy: download rate Mbps (maps to side-b-min-rate)", default=DOWNLOAD_RATE)
    parser.add_argument("--traffic_type", help="Legacy: download rate Mbps (maps to side-b-min-rate)", default=traffic_type)
    # Fine-grained traffic parameters (defaults match __init__)
    # parser.add_argument("--side-a-min-rate", type=int, default=0, help="Mbps (default: 0)")
    parser.add_argument("--side_a_max_rate", type=int, default=0, help="Mbps (default: 0)")
    # parser.add_argument("--side-b-min-rate", type=int, default=56, help="Mbps (default: 56)")
    parser.add_argument("--side_b_max_rate", type=int, default=0, help="Mbps (default: 0)")

    parser.add_argument("--side_a_min_pdu", type=int, default=-1, help="(default: -1)")
    parser.add_argument("--side_a_max_pdu", type=int, default=0, help="(default: 0)")
    parser.add_argument("--side_b_min_pdu", type=int, default=-1, help="(default: -1)")
    parser.add_argument("--side_b_max_pdu", type=int, default=0, help="(default: 0)")

    # Power control / WPS controller (defaults match __init__)
    parser.add_argument("--wifi_pdu", action="store_true", help="Use WifiPDU (default: False -> WebPowerSwitch)")
    parser.add_argument("--wps_username", default=WPS_USERNAME, help="WPS username (default: admin)")
    parser.add_argument("--wps_passwd", default=WPS_PASSWORD, help="WPS password (default: 1234)")
    if type(WPS_IP) != list:
        parser.add_argument("--wps_ip", default=WPS_IP, help="WPS/WifiPDU IP (default: 192.168.212.152)")
    parser.add_argument("--https", action="store_true", help="Use HTTPS to talk to WPS/WifiPDU (default: False)")
    parser.add_argument("--transient", action="store_true", help="Use transient power state (default: False)")
    parser.add_argument('--enable_motion_detection', help="If true will rotate the client", action='store_true')
    if type(WPS_IP) != list:
        parser.add_argument('--wps_outlets', type=str, default=WPS_OUTLETS, help='Outlets to turn ON (e.g. "1,2,3" or "1 2 3")')
    parser.add_argument("--client_mac", help="Client MAC address")
    args = parser.parse_args()
    print(f"Connecting to LANforge {args.mgr}:{args.port}")
    # lf.start()
    if type(WPS_IP) == list:
        args.wps_ip = WPS_IP
        args.wps_outlets = WPS_OUTLETS
    lf = ChamberLain(
        mgr=args.mgr,
        port=args.port,
        # Rates / PDUs
        side_a_min_rate=args.upload,
        side_a_max_rate=args.side_a_max_rate,
        side_b_min_rate=args.download,
        side_b_max_rate=args.side_b_max_rate,
        side_a_min_pdu=args.side_a_min_pdu,
        side_b_min_pdu=args.side_b_min_pdu,
        side_a_max_pdu=args.side_a_max_pdu,
        side_b_max_pdu=args.side_b_max_pdu,
        # Topology
        upstream_port=args.upstream_port,
        ssid=args.ssid,
        passwd=args.passwd,
        security_type=args.security,
        num_stations=args.num_stations,
        radio=args.radio,
        # Power control
        wifi_pdu=args.wifi_pdu,
        wps_username=args.wps_username,
        wps_passwd=args.wps_passwd,
        wps_ip=args.wps_ip,
        https=args.https,
        transient=args.transient,
        client_mac=args.client_mac,
        wps_outlets=args.wps_outlets,
        traffic_type=args.traffic_type,
        enable_motion_detection=args.enable_motion_detection
    )
    logger.info("Clearing existing stations and L3 CXs")
    lf.pre_cleanup()
    lf.start()
    lf.generate_report()


if __name__ == "__main__":
    main()
