"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2017. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Samer Deeb
@date:   Dec 20, 2017
"""

from __future__ import absolute_import, division, print_function

import csv
import os
import re

from cmlxztp.infra import conf_dir
from cmlxztp.dbmgr.params_compiler import ParamsCompiler


class DevConfig(object):

    def __init__(self, compiler, params):
        self._lines = compiler.translate(params)

    def save(self):
        pass


class DevParamsMgr(object):

    LOOP_PREFIX = 'LOOP<'
    LOOP_REGEX = re.compile(r'^LOOP<<(\w+)>>\:(.*)$')
    VAR_REGEX = re.compile(r'<<(\w+)>>')

    FIELD_NAMES = (
        # general
        'serial_num', 'part_num', 'role', 'hostname',
        # interfaces
        'interfaces', 'mgmt_interface', 'mgmt_ip', 'vrf_mgmt_ip',
        'vrf_mgmt_route', 'loopback_ip', 'l3_interface',
        'vlan_id', 'vlan_interface_ip', 'access_vlan_interfaces',
        'bridge_ports',
        # bgp
        'bgp_as', 'bgp_group', 'bgp_group_desc', 'bgp_group_type',
        'bgp_router_id', 'unnumbered_bgp_interfaces', 'bgp_interface',
        'bgp_unicast_network', 'bgp_aggregate_network',
        # ospf
        'ospf_area', 'ospf_authentication_key', 'ospf_authentication_method',
        'ospf_cost', 'ospf_deny_seq', 'ospf_metric', 'ospf_metric_type',
        'ospf_permit_network', 'ospf_network_type', 'ospf_permit_seq',
        'ospf_interfaces', 'ospf_prefix_list_name', 'ospf_router_id',
        # dhcp
        'dhcp_relay_interfaces', 'dhcp_relay_server',
        # dns
        'dns_server',
        # ntp
        'ntp_server', 'ntp_source_interface', 'time_zone',
        # syslog
        'syslog_server', 'syslog_port', 'syslog_protocol',
        # snmp
        'snmp_community', 'snmp_listening_address',
        )
    ROLE_TOR = 'tor'
    ROLE_SPINE = 'spine'
    ROLE_LEAF = 'leaf'
    ROLES = (ROLE_LEAF, ROLE_TOR, ROLE_SPINE)

    def __init__(self):
        self._repo = dict()
        self._read_csv()
        self._compilers = dict()
        self._compile_configurations()

    def _read_csv(self):
        csv_file_name = os.path.join(conf_dir, "switches.csv")
        with open(csv_file_name) as csvfile:
            reader = csv.DictReader(csvfile, self.FIELD_NAMES)
            next(reader, None)
            for row in reader:
                serial_num = row['serial_num'].upper()
                self._repo[serial_num] = row
        print (self._repo)

    def _compile_configurations(self):
        for role in self.ROLES:
            template_name = "%s.cfg" % role
            template_path = os.path.join(conf_dir, template_name)
            compiler = ParamsCompiler(template_path)
            compiler.compile()
            self._compilers[role] = compiler

    def dev_exists(self, dev_id):
        return dev_id in self._repo

    def get_dev_params(self, dev_id):
        return self._repo.get(dev_id)

    def get_dev_configuration(self, dev_params):
        role = dev_params.get('role')
        if not role:
            return
        compiler = self._compilers[role.lower()]
        dev_config = compiler.translate(dev_params)
        return dev_config


# pylint: disable=invalid-name
dev_params_mgr = DevParamsMgr()
# dev_params = dev_params_mgr.get_dev_params('MT1635X11021')
# print(dev_params)
# dev_params_mgr.get_dev_configuration(dev_params)
# dev_id = 'MT1635X11021'
# print (dev_params_mgr.get_dev_configuration(dev_id))
