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

#Traffic details
#IN MBPS
UPLOAD_RATE = 2
DOWNLOAD_RATE = 2

# WPS DETAILS
WPS_IP = ["192.168.212.56","192.168.212.57"]
WPS_USERNAME = "admin"
WPS_PASSWORD = "1234"
WPS_OUTLETS = [["1","3","4","5"],["1","2","3","4","5","8"]]
#WPS_OUTLETS = [["1"],["1"]]
WPS_AP_NAMES = {
    "WPS1" : {
    1: "Linksys E5400",
    2: "Eero 6+",
    3: "Google NEST WIFI Pro",
    4: "Starlink 232",
    5: "Tplink AX1800",
},
   "WPS2" : {
    1: "Linksys Atlas 6 (AX3000)",
    2: "Netgear Nighthawk AX6",
    3: "Arris Surf board (SB8200)",
    4: "Netgear NighthawkAC1900",
    5: "Tplink AXE5400",
    8: "Netgear RS280",
}
}


#PING DETAILS
PING_TIME = 10*60

#pass fail criteria
#Ping loss in %
EXPECTED_PING_LOSS_WITHOUT_LOAD = 1.5
EXPECTED_PING_LOSS_WITH_LOAD = 5

# Ping latency in ms 
EXPECTED_PING_LATENCY_WITHOUT_LOAD = 20
EXPECTED_PING_LATENCY_WITH_LOAD = 500

#IP fetch
IP_FETCH_INTERVAL = 5
IP_FETCH_RETRIES = 50


#for simulation
MAKE_SIMULATION = "yes"
LED_WPS_NUMBER = 6
LED_ON_OFF_INTERVAL = 10
LED_WPS_IP = "192.168.212.56"
"""
CONFIGURATION FORMAT GUIDE:

1. MGR
   - Type: string
   - Description: The LANforge Manager IP address.
   - Must be non-empty and in standard dotted IPv4 format.

2. PORT
   - Type: integer OR numeric string
   - Description: The HTTP port used by the LANforge Manager.
   - Must represent a positive number. Examples: 8080, "8080".

3. NO_OF_STATIONS
   - Type: integer
   - Description: The number of WiFi stations to create.
   - Must be a positive integer greater than zero.

4. WIPHY_RADIO
   - Type: string
   - Description: The target radio interface for creating stations.
   - Example: "wiphy0".

5. UPSTREAM_PORT
   - Type: string
   - Description: The wired upstream port for traffic (usually eth1).

6. TRAFFIC_TYPE
   - Type: string
   - Allowed values: "tcp" or "udp"
   - Description: Protocol for upload/download traffic generation.

7. UPLOAD_RATE
   - Type: integer OR numeric string
   - Description: Upload speed in Mbps.
   - Must be a positive number. Examples: 2, "2".

8. DOWNLOAD_RATE
   - Type: integer OR numeric string
   - Description: Download speed in Mbps.
   - Must be a positive number. Examples: 2, "2".

9. WPS_IP
   - Type: string
   - Description: The Web Power Switch (WPS) device IP.
   - Must be non-empty and valid IPv4.

10. WPS_USERNAME
    - Type: string
    - Description: Username for the WPS device.

12. WPS_OUTLETS
    - Type: string (comma-separated list)
    - Description: List of WPS outlet numbers to control.
    - Must contain only digits separated by commas.
    - Examples: "1,2,3", "4", "1,3,5"

13. PING_TIME
    - Type: integer
    - Description: Total duration for continuous ping (in seconds).
    - Must be greater than zero.

14. TIME_GAP
    - Type: integer
    - Description: Delay between periodic ping checks (in seconds).
    - Must be greater than zero.
"""

