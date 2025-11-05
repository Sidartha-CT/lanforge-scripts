import requests
from urllib import request
import logging
import sys
import json
import urllib
import time
import traceback
import re
from pprint import pformat, PrettyPrinter
debug_printer = PrettyPrinter(indent=2)

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(handlers=[logging.StreamHandler(stream=sys.stdout)], level=logging.INFO,
                    format='%(created)f %(levelname)-8s %(message)s %(filename)s %(lineno)s')
logging.propagate = False


MODE_2G = 15
UPLOAD_RATE = "2"
DOWNLOAD_RATE = "2"
TRAFFIC_TYPE = "lf_tcp"
DEBUG = False
logger = logging.getLogger(__name__)


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
            print(self.encode_url(req_url))
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
        if (response_json_list_ is not None):
            print("last")
        self.post_data = data
        if url[0] == '/':
            url = url[1:]
        req_url = self.pre_url + url
        responses = []
        if data is not None and data is not self.No_Data:
            print("with data", self.post_data)
            print("req url", req_url)
            print("encode url", self.encode_url(req_url))
            myrequest = request.Request(url=self.encode_url(req_url),
                                        method=method_,
                                        data=json.dumps(self.post_data).encode("utf-8"),
                                        headers=self.default_headers)
        else:
            print("without data")
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
            logger.error("LF post error")
            print("url", self.encode_url(req_url))
            print("data", data)
            traceback.print_exc()
            exit(0)
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
                logger.info('Found %s out of %s ports in %s out of %s tries in wait_until_ports_appear' % (len(found_stations), len(port_list), attempt, timeout / 2))
            else:
                logger.info('All %s ports appeared' % len(found_stations))
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
            print("name_to_eid wants eid like 1.1.sta0 but given[%s]" % eid_input)
            raise ValueError("name_to_eid wants eid like 1.1.sta0 but given[%s]" % eid_input)
        if type(eid_input) is not str:
            print(
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
        print("admin up called")
        # logger.info("186 admin_up port_eid: "+port_eid)
        eid = self.name_to_eid(port_eid)
        resource = eid[1]
        port = eid[2]
        print('eid', eid)
        request = self.port_up_request(resource_id=resource, port_name=port)
        print("request", request)
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
            print('eid inside')
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
                    logger.info(
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
                 side_a_min_pdu=-1, side_b_min_pdu=-1, side_a_max_pdu=0, side_b_max_pdu=0):
        super().__init__(lanforge_ip=mgr, port=port)
        self.station_list = None
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
        self.add_sta_flags = {
            "wpa_enable": 0x10,         # Enable WPA
            "custom_conf": 0x20,         # Use Custom wpa_supplicant config file.
            "wep_enable": 0x200,        # Use wpa_supplicant configured for WEP encryption.
            "wpa2_enable": 0x400,        # Use wpa_supplicant configured for WPA2 encryption.
            "ht40_disable": 0x800,        # Disable HT-40 even if hardware and AP support it.
            "scan_ssid": 0x1000,       # Enable SCAN-SSID flag in wpa_supplicant.
            "passive_scan": 0x2000,       # Use passive scanning (don't send probe requests).
            "disable_sgi": 0x4000,       # Disable SGI (Short Guard Interval).
            "lf_sta_migrate": 0x8000,       # OK-To-Migrate (Allow station migration between LANforge radios)
            "verbose": 0x10000,      # Verbose-Debug:  Increase debug info in wpa-supplicant and hostapd logs.
            "80211u_enable": 0x20000,      # Enable 802.11u (Interworking) feature.
            "80211u_auto": 0x40000,      # Enable 802.11u (Interworking) Auto-internetworking feature.  Always enabled currently.
            "80211u_gw": 0x80000,      # AP Provides access to internet (802.11u Interworking)
            "80211u_additional": 0x100000,     # AP requires additional step for access (802.11u Interworking)
            "80211u_e911": 0x200000,     # AP claims emergency services reachable (802.11u Interworking)
            "80211u_e911_unauth": 0x400000,     # AP provides Unauthenticated emergency services (802.11u Interworking)
            "hs20_enable": 0x800000,     # Enable Hotspot 2.0 (HS20) feature.  Requires WPA-2.
            "disable_gdaf": 0x1000000,    # AP:  Disable DGAF (used by HotSpot 2.0).
            "8021x_radius": 0x2000000,    # Use 802.1x (RADIUS for AP).
            "80211r_pmska_cache": 0x4000000,    # Enable oportunistic PMSKA caching for WPA2 (Related to 802.11r).
            "disable_ht80": 0x8000000,    # Disable HT80 (for AC chipset NICs only)
            "ibss_mode": 0x20000000,   # Station should be in IBSS mode.
            "osen_enable": 0x40000000,   # Enable OSEN protocol (OSU Server-only Authentication)
            "disable_roam": 0x80000000,   # Disable automatic station roaming based on scan results.
            "ht160_enable": 0x100000000,  # Enable HT160 mode.
            "disable_fast_reauth": 0x200000000,  # Disable fast_reauth option for virtual stations.
            "mesh_mode": 0x400000000,  # Station should be in MESH mode.
            "power_save_enable": 0x800000000,  # Station should enable power-save.  May not work in all drivers/configurations.
            "create_admin_down": 0x1000000000,  # Station should be created admin-down.
            "wds-mode": 0x2000000000,  # WDS station (sort of like a lame mesh), not supported on ath10k
            "no-supp-op-class-ie": 0x4000000000,  # Do not include supported-oper-class-IE in assoc requests.  May work around AP bugs.
            "txo-enable": 0x8000000000,  # Enable/disable tx-offloads, typically managed by set_wifi_txo command
            "use-wpa3": 0x10000000000,     # Enable WPA-3 (SAE Personal) mode.
            "use-bss-transition": 0x80000000000,     # Enable BSS transition.
            "ft-roam-over-ds": 0x800000000000,    # Roam over DS when AP supports it.
            "rrm-ignore-beacon-req": 0x1000000000000,   # Ignore (reject) RRM Beacon measurement request.
            "use-owe": 0x2000000000000,   # Enable OWE
            "be320-enable": 0x4000000000000,   # Enable 320Mhz mode.
            "disable-mlo": 0x8000000000000,   # Disable OFDMA
            "ignore-edca": 0x20000000000000,  # Request station to ignore EDCA settings
        }
        self.add_sta_modes = {
            "AUTO": 0,  # 802.11g
            "802.11a": 1,  # 802.11a
            "b": 2,  # 802.11b
            "g": 3,  # 802.11g
            "abg": 4,  # 802.11abg
            "abgn": 5,  # 802.11abgn
            "bgn": 6,  # 802.11bgn
            "bg": 7,  # 802.11bg
            "abgnAC": 8,  # 802.11abgn-AC
            "anAC": 9,  # 802.11an-AC
            "an": 10,  # 802.11an
            "bgnAC": 11,  # 802.11bgn-AC
            "abgnAX": 12,  # 802.11abgn-AX, a/b/g/n/AC/AX (dual-band AX) support
            "bgnAX": 13,  # 802.11bgn-AX
            "anAX": 14,  # 802.11an-AX
            "aAX": 15,  # 802.11a-AX (6E disables /n and /ac)
            "abgn7": 16,  # 802.11abgn-EHT  a/b/g/n/AC/AX/EHT (dual-band AX) support
            "bgn7": 17,  # 802.11bgn-EHT
            "an7": 18,  # 802.11an-EHT
            "a7": 19  # 802.11a-EHT (6E disables /n and /ac)
        }
        self.set_port_interest_flags = {
            "command_flags": 0x1,               # apply command flags
            "current_flags": 0x2,               # apply current flags
            "ip_address": 0x4,               # IP address
            "ip_Mask": 0x8,               # IP mask
            "ip_gateway": 0x10,              # IP gateway
            "mac_address": 0x20,              # MAC address
            "supported_flags": 0x40,              # apply supported flags
            "link_speed": 0x80,              # Link speed
            "mtu": 0x100,             # MTU
            "tx_queue_length": 0x200,             # TX Queue Length
            "promisc_mode": 0x400,             # PROMISC mode
            "interal_use_1": 0x800,             # (INTERNAL USE)
            "alias": 0x1000,            # Port alias
            "rx_all": 0x2000,            # Rx-ALL
            "dhcp": 0x4000,            # including client-id.
            "rpt_timer": 0x8000,            # Report Timer
            "bridge": 0x10000,           # BRIDGE
            "ipv6_addrs": 0x20000,           # IPv6 Address
            "bypass": 0x40000,           # Bypass
            "gen_offload": 0x80000,           # Generic offload flags, everything but LRO
            "cpu_mask": 0x100000,          # CPU Mask, useful for pinning process to CPU core
            "lro_offload": 0x200000,          # LRO (Must be disabled when used in Wanlink,
            # and probably in routers)

            "sta_br_id": 0x400000,          # WiFi Bridge identifier.  0 means no bridging.
            "ifdown": 0x800000,          # Down interface
            "dhcpv6": 0x1000000,         # Use DHCPv6
            "rxfcs": 0x2000000,         # RXFCS
            "dhcp_rls": 0x4000000,         # DHCP release
            "svc_httpd": 0x8000000,         # Enable/disable HTTP Service for a port
            "svc_ftpd": 0x10000000,        # Enable/disable FTP Service for a port
            "aux_mgt": 0x20000000,        # Enable/disable Auxillary-Management for a port
            "no_dhcp_conn": 0x40000000,        # Enable/disable NO-DHCP-ON-CONNECT flag for a port
            "no_apply_dhcp": 0x80000000,        # Enable/disable NO-APPLY-DHCP flag for a port
            "skip_ifup_roam": 0x100000000,       # Enable/disable SKIP-IFUP-ON-ROAM flag for a port
        }
        self.set_port_current_flags = {
            "if_down": 0x1,  # Interface Down
            "fixed_10bt_hd": 0x2,  # Fixed-10bt-HD (half duplex)
            "fixed_10bt_fd": 0x4,  # Fixed-10bt-FD
            "fixed_100bt_hd": 0x8,  # Fixed-100bt-HD
            "fixed_100bt_fd": 0x10,  # Fixed-100bt-FD
            "auto_neg": 0x100,  # auto-negotiate
            "adv_10bt_hd": 0x100000,  # advert-10bt-HD
            "adv_10bt_fd": 0x200000,  # advert-10bt-FD
            "adv_100bt_hd": 0x400000,  # advert-100bt-HD
            "adv_100bt_fd": 0x800000,  # advert-100bt-FD
            "adv_flow_ctl": 0x8000000,  # advert-flow-control
            "promisc": 0x10000000,  # PROMISC
            "use_dhcp": 0x80000000,  # USE-DHCP
            "adv_10g_hd": 0x400000000,  # advert-10G-HD
            "adv_10g_fd": 0x800000000,  # advert-10G-FD
            "tso_enabled": 0x1000000000,  # TSO-Enabled
            "lro_enabled": 0x2000000000,  # LRO-Enabled
            "gro_enabled": 0x4000000000,  # GRO-Enabled
            "ufo_enabled": 0x8000000000,  # UFO-Enabled
            "gso_enabled": 0x10000000000,  # GSO-Enabled
            "use_dhcpv6": 0x20000000000,  # USE-DHCPv6
            "rxfcs": 0x40000000000,  # RXFCS
            "no_dhcp_rel": 0x80000000000,  # No-DHCP-Release
            "staged_ifup": 0x100000000000,  # Staged-IFUP
            "http_enabled": 0x200000000000,  # Enable HTTP (nginx) service for this port.
            "ftp_enabled": 0x400000000000,  # Enable FTP (vsftpd) service for this port.
            "aux_mgt": 0x800000000000,  # Enable Auxillary-Management flag for this port.
            "no_dhcp_restart": 0x1000000000000,  # Disable restart of DHCP on link connect (ie, wifi).
            # This should usually be enabled when testing wifi
            # roaming so that the wifi station can roam
            # without having to re-acquire a DHCP lease each
            # time it roams.
            "ignore_dhcp": 0x2000000000000,  # Don't set DHCP acquired IP on interface,
            # instead print CLI text message. May be useful
            # in certain wifi-bridging scenarios where external
            # traffic-generator cannot directly support DHCP.

            "no_ifup_post": 0x4000000000000,  # Skip ifup-post script if we can detect that we
            # have roamed. Roaming  is considered true if
            # the IPv4 address has not changed.

            "radius_enabled": 0x20000000000000,  # Enable RADIUS service (using hostapd as radius server)
            "ipsec_client": 0x40000000000000,  # Enable client IPSEC xfrm on this port.
            "ipsec_concentrator": 0x80000000000000,  # Enable concentrator (upstream) IPSEC xfrm on this port.
            "service_dns": 0x100000000000000,  # Enable DNS (dnsmasq) service on this port.
            "adv_5g_fd": 0x400000000000000,  # Advertise 5Gbps link speed.
        }
        self.desired_set_port_current_flags = ["if_down"]
        self.desired_set_port_interest_flags = ["current_flags", "ifdown"]
        self.wifi_extra_data_modified = False
        self.wifi_extra_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "key_mgmt": None,
            "eap": None,
            "hessid": None,
            "identity": None,
            "password": None,
            "realm": None,
            "domain": None
        }
        self.wifi_extra2_data_modified = False
        self.wifi_extra2_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "req_flush": None,
            "ignore_probe": None,
            "ignore_auth": None,
            "ignore_assoc": None,
            "ignore_reassoc": None,
            "post_ifup_script": None,
            "ocsp": 0,
            "venue_id": None,
            "initial_band_pref": 0,
            "bss_color": None
        }
        self.wifi_txo_data_modified = False
        self.wifi_txo_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "txo_enable": None,
            "txo_txpower": None,
            "txo_pream": None,
            "txo_mcs": None,
            "txo_nss": None,
            "txo_bw": None,
            "txo_retries": None,
            "txo_sgi": None
        }

        self.reset_port_extra_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "test_duration": 0,
            "reset_port_enable": False,
            "reset_port_time_min": 0,
            "reset_port_time_max": 0,
            "reset_port_timer_started": False,
            "port_to_reset": 0,
            "seconds_till_reset": 0
        }
        pass

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

    def wait_for_ip(self, station_list=None, ipv4=True, ipv6=False, timeout_sec=360, debug=False):
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
                    logger.info("station_list: incomplete response for eid: %s:  wait longer" % sta_eid)
                    logger.info(pformat(response))
                    print(eid)
                    exit(0)
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
                    logger.info('%s did not acquire IPv4 addresses' % stas_without_ip4s.keys())
                if len(stas_without_ip6s) > 0:
                    logger.info('%s did not acquire IPv6 addresses' % stas_without_ip6s.keys())
                port_info = self.json_get('/port/all')
                logger.debug(pformat(port_info))
            return False
        else:
            if debug:
                logger.debug("Found IPs for all requested ports.")
            return True

    def create_station(self, num_stations, ssid, passwd, security_type, radio, mode=MODE_2G):
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
        prefix = "sta"
        start_id = 0
        end_id = num_stations  # total-1
        # self.station_list = self.port_name_series(prefix=prefix,start_id=start_id,end_id=end_id-1,radio=radio)
        self.station_list = self.port_name_series(prefix=prefix, start_id=start_id, end_id=end_id - 1, radio=None)
        print("Stations to create: {}".format(self.station_list))
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
            print("Station creation FAILED")
        if not self.wait_for_ip(self.station_list, timeout_sec=60):
            print("Stations failed to get IP")
            exit(1)
        else:
            print("all stations got IP")

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
        for eidn in my_sta_eids:
            if eidn in self.station_names:
                logger.info("Station {eidn} already created, skipping.".format(eidn=eidn))
                continue
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
            self.json_post(url=add_sta_r_url, data=add_sta_data)
            finished_sta.append(eidn)
            # if debug:
            #     logger.debug("- ~3264 - {eidn} - add_sta_r.jsonPost - - - - - - - - - - - - - - - - - - ".format(eidn=eidn))
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
        print(cx_list)
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
        logger.info("Starting CXs...")
        for cx_name in cx_list:
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


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Create Wi-Fi Stations using LANforge"
    )

    parser.add_argument("--mgr",
                        required=True,
                        help="LANforge Manager IP")

    parser.add_argument("--port",
                        type=int,
                        default=8080,
                        help="LANforge HTTP port (default: 8080)")

    parser.add_argument("--ssid",
                        required=True,
                        help="SSID of the WiFi network")

    parser.add_argument("--passwd",
                        required=True,
                        help="WiFi password")

    parser.add_argument("--security",
                        choices=["open", "wep", "wpa", "wpa2", "wpa3", "owe"],
                        default="wpa2",
                        help="Wi-Fi security mode")

    parser.add_argument("--num_stations",
                        type=int,
                        required=True,
                        help="Number of stations to create")

    parser.add_argument("--radio",
                        required=True,
                        help="Radio interface, e.g. wiphy0, wiphy1")

    args = parser.parse_args()

    print(f"Connecting to LANforge {args.mgr}:{args.port}")

    lf = ChamberLain(args.mgr, port=args.port)

    # override default radio in class call
    lf.create_station(
        num_stations=args.num_stations,
        ssid=args.ssid,
        passwd=args.passwd,
        security_type=args.security,
        radio=args.radio
    )
    # lf.generate_l3_traffic()
    port_lists = []
    eid_list = []
    print(lf.station_list)
    for i in lf.station_list:
        # print(lf.name_to_eid(i))
        eid = lf.name_to_eid(i)
        eid_list.append(eid)
        port_lists.append('.'.join(str(x) for x in eid if x))
    print(port_lists)
    print(eid_list)
    count = 0
    traffic_type = TRAFFIC_TYPE
    # logger.info("Creating connections for endpoint type: %s cx-count: %s" % (
    for station in range(len(port_lists)):
        logger.info("Creating connections for endpoint type: %s cx-count: %s" % (
            traffic_type, count))
        lf.generate_l3_traffic(endp_type=traffic_type, side_a=[port_lists[station]],
                               side_b="eth1", cx_name="%s" % (lf.station_list[count]), upload_rate=UPLOAD_RATE, download_rate=DOWNLOAD_RATE)
        count += 1

    lf.start_specific(lf.created_cx)


if __name__ == "__main__":
    main()
