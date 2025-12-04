DUT_NAME = "myQ Wireless Security Outdoor Camera"

# LANFORGE DETAILS
MGR = "192.168.212.55"
PORT = "8080"
SSID = "Interop-2G"
PASSWORD = "Password@123"
SECURITY = "wpa2"
#stations
NO_OF_STATIONS = 10
WIPHY_RADIO = "wiphy0"
UPSTREAM_PORT = "eth1"
TRAFFIC_TYPE = "tcp"

# Traffic details (Mbps)
UPLOAD_RATE = 2
DOWNLOAD_RATE = 2

# WPS DETAILS
WPS_IP = ["192.168.212.56", "192.168.212.57", "192.168.212.152"]
WPS_USERNAME = "admin"
WPS_PASSWORD = "1234"
WPS_OUTLETS = [["1","2","3","4","5"],["1","2","3","4","5","8"],["1","2"]]
#WPS_OUTLETS = [["1"],["5"],["1"]]
WPS_AP_NAMES = {
    "WPS1": {
        1: "Linksys E5400",
        2: "Eero 6+",
        3: "Google NEST WIFI Pro",
        4: "Starlink 232",
        5: "Tplink AX1800",
    },
    "WPS2": {
        1: "Linksys Atlas 6 (AX3000)",
        2: "Netgear Nighthawk AX6",
        3: "Arris Surf board (SB8200)",
        4: "Netgear NighthawkAC1900",
        5: "Tplink AXE5400",
        8: "Netgear RS280",
    },
    "WPS3": {
        1: "Tplink AX1800_2",
        2: "ROG GT-BE98 Pro",
    }
}


#PING DETAILS
PING_TIME = 1*60

# Pass-fail criteria
EXPECTED_PING_LOSS_WITHOUT_LOAD = 1.5
EXPECTED_PING_LOSS_WITH_LOAD = 5

# Ping latency in ms 
EXPECTED_PING_LATENCY_WITHOUT_LOAD = 20
EXPECTED_PING_LATENCY_WITH_LOAD = 500

# IP fetch
IP_FETCH_INTERVAL = 5
IP_FETCH_RETRIES = 50

# Rotator
ROTATOR_WPS_NUMBER = 6
ROTATOR_WPS_IP = "192.168.212.56"

"""
COMPLETE CONFIGURATION FORMAT GUIDE:

1. DUT_NAME
   - Type: string
   - Description: Name of the Device Under Test.

2. MGR
   - Type: string (IPv4)
   - Description: LANforge Manager IP.

3. PORT
   - Type: integer or numeric string
   - Description: LANforge REST port.

4. SSID / PASSWORD / SECURITY
   - Type: string
   - Description: WiFi credentials for station connection.
   - SECURITY allowed: "wpa2", "wpa3", "open".


5. NO_OF_STATIONS
   - Type: integer (>0)
   - Description: Number of WiFi stations.

6. WIPHY_RADIO
   - Type: string
   - Description: Radio used for station creation.

7. UPSTREAM_PORT
    - Type: string
    - Description: Wired port for upstream link.

8. TRAFFIC_TYPE
    - Type: string
    - Allowed: "tcp" or "udp".

9. UPLOAD_RATE / DOWNLOAD_RATE
    - Type: integer or numeric string
    - Description: Mbps traffic speeds.

10. WPS_IP
    - Type: list of strings
    - Description: IPs of Web Power Switch devices.

11. WPS_USERNAME / WPS_PASSWORD
    - Type: string
    - Description: Login credentials for WPS.

12. WPS_OUTLETS
    - Type: list of lists
    - Each inner list contains outlet numbers as strings.

13. WPS_AP_NAMES
    - Type: dict
    - Maps each WPS to AP names per outlet index.

14. PING_TIME
    - Type: integer (>0)
    - Description: Duration for continuous ping.

15. EXPECTED_PING_LOSS_WITHOUT_LOAD / WITH_LOAD
    - Type: float
    - Max allowed ping loss %.

16. EXPECTED_PING_LATENCY_WITHOUT_LOAD / WITH_LOAD
    - Type: integer
    - Max allowed ping latency in ms.

17. IP_FETCH_INTERVAL
    - Type: integer
    - Time interval between retries.

18. IP_FETCH_RETRIES
    - Type: integer
    - Max retries before failure.

19. ROTATOR_WPS_NUMBER
    - Type: integer
    - WPS outlet number for camera rotator.

20. ROTATOR_WPS_IP
    - Type: string
    - IP address of rotator WPS.
"""
