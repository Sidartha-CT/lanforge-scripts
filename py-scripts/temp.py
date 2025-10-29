def run_ftp_test1(args):
    # set up logger
    logger_config = lf_logger_config.lf_logger_config()
    if args.lf_logger_config_json:
        # logger_config.lf_logger_config_json = "lf_logger_config.json"
        logger_config.lf_logger_config_json = args.lf_logger_config_json
        logger_config.load_lf_logger_config()

    # 1st time stamp for test duration
    time_stamp1 = datetime.now()

    # use for creating ftp_test dictionary
    interation_num = 0

    # empty dictionary for whole test data
    ftp_data = {}

    def pass_fail_duration(band, file_size):
        '''Method for set duration according file size and band which are given by user'''

        if band == "2.4G":
            if len(args.file_sizes) is not len(args.twog_duration):
                raise Exception("Give proper Pass or Fail duration for 2.4G band")

            for size in args.file_sizes:
                if size == file_size:
                    index = list(args.file_sizes).index(size)
                    duration = args.twog_duration[index]
        elif band == "5G":
            if len(args.file_sizes) is not len(args.fiveg_duration):
                raise Exception("Give proper Pass or Fail duration for 5G band")
            for size in args.file_sizes:
                if size == file_size:
                    index = list(args.file_sizes).index(size)
                    duration = args.fiveg_duration[index]
        else:
            if len(args.file_sizes) is not len(args.both_duration):
                raise Exception("Give proper Pass or Fail duration for 5G band")
            for size in args.file_sizes:
                if size == file_size:
                    index = list(args.file_sizes).index(size)
                    duration = args.both_duration[index]
        if duration.isdigit():
            duration = int(duration)
        else:
            duration = float(duration)

        return duration

    validate_args(args)
    if args.traffic_duration.endswith('s') or args.traffic_duration.endswith('S'):
        args.traffic_duration = int(args.traffic_duration[0:-1])
    elif args.traffic_duration.endswith('m') or args.traffic_duration.endswith('M'):
        args.traffic_duration = int(args.traffic_duration[0:-1]) * 60
    elif args.traffic_duration.endswith('h') or args.traffic_duration.endswith('H'):
        args.traffic_duration = int(args.traffic_duration[0:-1]) * 60 * 60
    elif args.traffic_duration.endswith(''):
        args.traffic_duration = int(args.traffic_duration)

    # For all combinations ftp_data of directions, file size and client counts, run the test
    for band in args.bands:
        for direction in args.directions:
            for file_size in args.file_sizes:
                # Start Test
                obj = FtpTest(lfclient_host=args.mgr,
                              lfclient_port=args.mgr_port,
                              result_dir=args.result_dir,
                              upstream=args.upstream_port,
                              dut_ssid=args.ssid,
                              group_name=args.group_name,
                              profile_name=args.profile_name,
                              file_name=args.file_name,
                              dut_passwd=args.passwd,
                              dut_security=args.security,
                              num_sta=args.num_stations,
                              band=band,
                              ap_name=args.ap_name,
                              file_size=file_size,
                              direction=direction,
                              twog_radio=args.twog_radio,
                              fiveg_radio=args.fiveg_radio,
                              sixg_radio=args.sixg_radio,
                              lf_username=args.lf_username,
                              lf_password=args.lf_password,
                              # duration=pass_fail_duration(band, file_size),
                              traffic_duration=args.traffic_duration,
                              ssh_port=args.ssh_port,
                              clients_type=args.clients_type,
                              dowebgui=args.dowebgui,
                              device_list=args.device_list,
                              test_name=args.test_name,
                              eap_method=args.eap_method,
                              eap_identity=args.eap_identity,
                              ieee80211=args.ieee8021x,
                              ieee80211u=args.ieee80211u,
                              ieee80211w=args.ieee80211w,
                              enable_pkc=args.enable_pkc,
                              bss_transition=args.bss_transition,
                              power_save=args.power_save,
                              disable_ofdma=args.disable_ofdma,
                              roam_ft_ds=args.roam_ft_ds,
                              key_management=args.key_management,
                              pairwise=args.pairwise,
                              private_key=args.private_key,
                              ca_cert=args.ca_cert,
                              client_cert=args.client_cert,
                              pk_passwd=args.pk_passwd,
                              pac_file=args.pac_file,
                              expected_passfail_val=args.expected_passfail_value,
                              csv_name=args.device_csv_name,
                              wait_time=args.wait_time,
                              config=args.config,
                              get_live_view= args.get_live_view,
                              total_floors = args.total_floors
                              )

                interation_num = interation_num + 1
                obj.file_create()
                if args.clients_type == "Real":
                    if not isinstance(args.device_list, list):
                        obj.device_list = obj.filter_iOS_devices(args.device_list)
                        if len(obj.device_list) == 0:
                            logger.info("There are no devices available")
                            exit(1)
                    configured_device, configuration = obj.query_realclients()

                if args.dowebgui and args.group_name:
                    # If no devices are configured,update the Web UI with "Stopped" status
                    if len(configured_device) == 0:
                        logger.warning("No device is available to run the test")
                        obj1 = {
                            "status": "Stopped",
                            "configuration_status": "configured"
                        }
                        obj.updating_webui_runningjson(obj1)
                        return
                    # If devices are configured, update the Web UI with the list of configured devices
                    else:
                        obj1 = {
                            "configured_devices": configured_device,
                            "configuration_status": "configured"
                        }
                        obj.updating_webui_runningjson(obj1)
                obj.set_values()
                obj.precleanup()
                obj.build()
                if not obj.passes():
                    logger.info(obj.get_fail_message())
                    exit(1)

                if obj.clients_type == 'Real':
                    obj.monitor_cx()
                    logger.info(f'Test started on the devices : {obj.input_devices_list}')
                # First time stamp
                time1 = datetime.now()
                logger.info("Traffic started running at %s", time1)
                obj.start(False, False)
                # to fetch runtime values during the execution and fill the csv.
                if args.dowebgui or args.clients_type == "Real":
                    obj.monitor_for_runtime_csv()
                    obj.my_monitor_for_real_devices()
                else:
                    time.sleep(args.traffic_duration)
                    obj.my_monitor()

                # # return list of download/upload completed time stamp
                # time_list = obj.my_monitor(time1)
                # # print("pass_fail_duration - time_list:{time_list}".format(time_list=time_list))
                # # check pass or fail
                # pass_fail = obj.pass_fail_check(time_list)

                # # dictionary of whole data
                # ftp_data[interation_num] = obj.ftp_test_data(time_list, pass_fail, args.bands, args.file_sizes,
                #                                              args.directions, args.num_stations)
                # # print("pass_fail_duration - ftp_data:{ftp_data}".format(ftp_data=ftp_data))
                obj.stop()
                print("Traffic stopped running")

                obj.postcleanup()
                time2 = datetime.now()
                logger.info("Test ended at %s", time2)

    # 2nd time stamp for test duration
    time_stamp2 = datetime.now()

    # total time for test duration
    # test_duration = str(time_stamp2 - time_stamp1)[:-7]

    date = str(datetime.now()).split(",")[0].replace(" ", "-").split(".")[0]

    # print(ftp_data)

    input_setup_info = {
        "AP IP": args.ap_ip,
        "File Size": args.file_sizes,
        "Bands": args.bands,
        "Direction": args.directions,
        "Stations": args.num_stations,
        "Upstream": args.upstream_port,
        "SSID": args.ssid,
        "Security": args.security,
        "Contact": "support@candelatech.com"
    }
    if args.dowebgui:
        obj.data_for_webui["status"] = ["STOPPED"] * len(obj.url_data)

        df1 = pd.DataFrame(obj.data_for_webui)
        df1.to_csv('{}/ftp_datavalues.csv'.format(obj.result_dir), index=False)
        # copying to home directory i.e home/user_name
        # obj.copy_reports_to_home_dir()
    # Report generation when groups are specified
    if args.group_name:
        obj.generate_report(ftp_data, date, input_setup_info, test_rig=args.test_rig,
                            test_tag=args.test_tag, dut_hw_version=args.dut_hw_version,
                            dut_sw_version=args.dut_sw_version, dut_model_num=args.dut_model_num,
                            dut_serial_num=args.dut_serial_num, test_id=args.test_id,
                            bands=args.bands, csv_outfile=args.csv_outfile, local_lf_report_dir=args.local_lf_report_dir, config_devices=configuration)
    # Generating report without group-specific device configuration
    else:
        obj.generate_report(ftp_data, date, input_setup_info, test_rig=args.test_rig,
                            test_tag=args.test_tag, dut_hw_version=args.dut_hw_version,
                            dut_sw_version=args.dut_sw_version, dut_model_num=args.dut_model_num,
                            dut_serial_num=args.dut_serial_num, test_id=args.test_id,
                            bands=args.bands, csv_outfile=args.csv_outfile, local_lf_report_dir=args.local_lf_report_dir)

    if args.dowebgui:
        obj.copy_reports_to_home_dir()
