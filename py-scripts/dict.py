ADD_STA_FLAGS = {
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

ADD_STA_MODES = {
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

SET_PORT_INTREST_FLAGS = {
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

SET_PORT_CURRENT_FLAGS = {
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
WIFI_EXTRA_DATA = {
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
WIFI_EXTRA2_DATA = {
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
WIFI_TXO_DATA = {
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
RESET_PORT_EXTRA_DATA = {
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

