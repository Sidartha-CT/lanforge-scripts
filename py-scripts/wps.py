#!/usr/bin/env python3
"""This module defines the WPS (Web Power Switch) functionalities."""

"""
wps.py

Control Web Power Switch outlets via REST API or simple Wi-Fi PDU HTTP.

Requires:
    pip install requests

Usage examples:
    # Standard WebPowerSwitch (REST API)
    python wps.py --ip 192.168.212.151 --all-off
    python wps.py --ip 192.168.212.151 --on 1,3 --off 2
    python wps.py --ip 192.168.212.151 --setup 2

    # Simple Wi-Fi PDU (no auth) with 4 outlets
    python wps.py --wifi --ip 192.168.210.100 --all-on
    python wps.py --wifi --ip 192.168.210.100 --on 1,4
"""

import argparse
import sys
import requests
from requests.auth import HTTPDigestAuth

class WebPowerSwitch:
    def __init__(self, ip, username='admin', password='1234', use_https=False):
        self.ip = ip
        self.username = username
        self.password = password
        scheme = 'https' if use_https else 'http'
        self.relay_url = f"{scheme}://{self.ip}/restapi/relay"
        self.config_url = f"{scheme}://{self.ip}/restapi/config"
        self.auth = HTTPDigestAuth(self.username, self.password)
        self.common_headers = {
            'X-CSRF': 'x',
            'Accept': 'application/json',
        }

    def set_outlet(self, index, state, persistent=True):
        """
        Set a single outlet ON/OFF (REST API).
        index: 0-based (0..N-1)
        state: True=ON, False=OFF
        persistent: persistent or transient
        """
        path = f"outlets/{index}/state/" if persistent else f"outlets/{index}/transient_state/"
        url = f"{self.relay_url}/{path}"
        data = {'value': 'true' if state else 'false'}
        headers = {**self.common_headers, 'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.put(url, auth=self.auth, headers=headers, data=data)
        resp.raise_for_status()
        return resp

    def set_all(self, state, persistent=True):
        """
        Set all outlets ON/OFF (REST API).
        """
        path = "outlets/all;/state/" if persistent else "outlets/all;/transient_state/"
        url = f"{self.relay_url}/{path}"
        data = {'value': 'true' if state else 'false'}
        headers = {**self.common_headers, 'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.put(url, auth=self.auth, headers=headers, data=data)
        resp.raise_for_status()
        return resp

    def set_recovery_mode(self, mode):
        """
        Configure power-loss recovery (0=all-off,1=all-on,2=restore last state).
        """
        url = f"{self.config_url}/power_on_recovery/"
        data = {'value': str(mode)}
        headers = {**self.common_headers, 'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.put(url, auth=self.auth, headers=headers, data=data)
        resp.raise_for_status()
        return resp

class WifiPDU:
    def __init__(self, ip, max_outlets=4, use_https=False):
        self.ip = ip
        scheme = 'https' if use_https else 'http'
        self.base_url = f"{scheme}://{self.ip}"
        self.max_outlets = max_outlets

    def set_outlet(self, index, state):
        """
        Control simple Wi-Fi PDU via HTTP GET.
        index: 0-based (0..max_outlets-1)
        state: True=ON, False=OFF
        """
        if index < 0 or index >= self.max_outlets:
            print(f"Warning: outlet {index+1} exceeds max {self.max_outlets}, skipping")
            return
        action = 'on' if state else 'off'
        url = f"{self.base_url}/{index+1}/{action}"
        # Use GET to trigger, HEAD to confirm
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        # Optionally HEAD for faster confirmation
        requests.head(url, timeout=2)
        print(f"turned {action} all switches")
        return r

    def set_all(self, state):
        """
        Set all outlets ON/OFF for Wi-Fi PDU.
        """
        for idx in range(self.max_outlets):
            self.set_outlet(idx, state)
        return None


def parse_outlets(s):
    """
    Convert a comma or space separated list of outlet numbers (1,2,3 or "1 2 3") into
    a sorted list of unique integers >=1.
    """
    seen = set()
    result = []
    if not s:
        return result
    for token in s.replace(',', ' ').split():
        try:
            num = int(token)
            if num >= 1 and num not in seen:
                seen.add(num)
                result.append(num)
        except ValueError:
            continue
    return sorted(result)


def main():
    parser = argparse.ArgumentParser(description='Web Power Switch / Wi-Fi PDU Controller')
    parser.add_argument('--ip', '-i', default='192.168.212.151',
                        help='Device IP address (default: %(default)s)')
    parser.add_argument('--wifi', action='store_true',
                        help='Use simple Wi-Fi PDU (no auth, HTTP GET to /<n>/on|off)')
    parser.add_argument('--user', '-u', default='admin',
                        help='Username for REST API (default: %(default)s)')
    parser.add_argument('--password', '-p', default='1234',
                        help='Password for REST API (default: %(default)s)')
    parser.add_argument('--https', action='store_true',
                        help='Use HTTPS instead of HTTP')
    parser.add_argument('--on', type=str, default='',
                        help='Outlets to turn ON (e.g. "1,2,3" or "1 2 3")')
    parser.add_argument('--off', type=str, default='',
                        help='Outlets to turn OFF (e.g. "4,5,6" or "4 5 6")')
    parser.add_argument('--all-on', action='store_true',
                        help='Turn all outlets ON')
    parser.add_argument('--all-off', action='store_true',
                        help='Turn all outlets OFF')
    parser.add_argument('--transient', action='store_true',
                        help='Use transient state (REST API only)')
    parser.add_argument('--setup', type=int, choices=[0,1,2],
                        help='Configure power-loss recovery 0=off,1=on,2=restore (REST API only)')
    args = parser.parse_args()

    on_outlets = parse_outlets(args.on)
    off_outlets = parse_outlets(args.off)

    # Validate flags
    if args.setup is not None and (args.on or args.off or args.all_on or args.all_off):
        print("Error: --setup cannot be combined with on/off commands")
        sys.exit(1)
    if args.all_on and args.all_off:
        print("Error: --all-on and --all-off cannot be used together")
        sys.exit(1)
    if (args.all_on or args.all_off) and (on_outlets or off_outlets):
        print("Error: cannot mix --all-on/--all-off with --on/--off")
        sys.exit(1)
    if not (args.setup is not None or args.all_on or args.all_off or on_outlets or off_outlets):
        print("Error: specify --setup, --all-on, --all-off, --on, or --off")
        sys.exit(1)

    # Instantiate appropriate controller
    if args.wifi:
        controller = WifiPDU(args.ip, use_https=args.https)
        persistent = True  # transient not supported
    else:
        controller = WebPowerSwitch(args.ip, args.user, args.password, use_https=args.https)
        persistent = not args.transient

    try:
        if not args.wifi and args.setup is not None:
            controller.set_recovery_mode(args.setup)
            print(f"Power-loss recovery mode set to {args.setup}")
        elif args.all_on:
            controller.set_all(True, persistent=persistent) if not args.wifi else controller.set_all(True)
            print("All outlets turned ON")
        elif args.all_off:
            controller.set_all(False, persistent=persistent) if not args.wifi else controller.set_all(False)
            print("All outlets turned OFF")
        else:
            # Individual outlets
            for o in on_outlets:
                print(f"Turning ON outlet {o}")
                if args.wifi:
                    controller.set_outlet(o-1, True)
                else:
                    controller.set_outlet(o-1, True, persistent=persistent)
            for o in off_outlets:
                print(f"Turning OFF outlet {o}")
                if args.wifi:
                    controller.set_outlet(o-1, False)
                else:
                    controller.set_outlet(o-1, False, persistent=persistent)
            print("Operations completed")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == '__main__':
    main()
