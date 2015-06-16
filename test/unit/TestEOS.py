# Copyright 2014 Spotify AB. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import unittest

from pyEOS import EOS
import pyEOS.exceptions as exceptions

import config


class TestEOS(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.device = EOS(config.hostname, config.username, config.password, config.use_ssl)
        cls.device.open()

    @classmethod
    def tearDownClass(cls):
        cls.device.close()

    def test_dynamic_show_command(self):
        lldp = self.device.show_lldp_neighbors()
        self.assertGreater(len(lldp), 0)

    def test_dynamic_show_command_format_text(self):
        lldp = self.device.show_lldp_neighbors(format='text')['output']
        self.assertGreater(len(lldp), 0)

    def test_dynamic_show_command_unconverted(self):
        # It has to be an unconverted command
        kernel = self.device.show_kernel_interface_addr(auto_format=True)['output']
        self.assertGreater(len(kernel), 0)

    def test_dynamic_show_command_raises_unconverted(self):
        self.assertRaises(exceptions.CommandUnconverted, self.device.show_kernel_interface_addr)

    def test_wrong_command(self):
        self.assertRaises(exceptions.CommandError, self.device.show_ip_rout)

    def test_arbitrary_command(self):
        output = self.device.run_commands(['dir /all'])[1]['messages'][0]
        self.assertGreater(len(output), 0)

    def test_loading_config(self):
        self.device.load_candidate_config(filename='configs/new_good.conf')
        self.device.replace_config()
        diff = self.device.compare_config()

        # Reverting changes
        self.device.load_candidate_config(filename='configs/initial.conf')
        self.device.replace_config()
        self.assertEqual(len(diff), 0)

    def test_loading_config_with_typo(self):
        self.device.load_candidate_config(filename='configs/new_typo.conf')
        self.assertRaises(exceptions.ConfigReplaceError, self.device.replace_config)

    def test_loading_modified_config_and_diff(self):
        intended_diff = '--- system:/running-config\n+++ session:/pyeos-diff-session-config\n@@ -4,7 +4,7 @@\n !\n transceiver qsfp default-mode 4x10G\n !\n-hostname pyeos-unittest\n+hostname pyeos-unittest-changed\n !\n spanning-tree mode mstp\n !\n@@ -19,7 +19,7 @@\n interface Ethernet1\n !\n interface Ethernet2\n-   description bla\n+   description ble\n !\n interface Ethernet3\n !\n@@ -32,12 +32,12 @@\n !\n router bgp 65000\n    vrf test\n-      neighbor 1.1.1.1 remote-as 1\n-      neighbor 1.1.1.1 maximum-routes 12000 \n+      neighbor 1.1.1.2 remote-as 1\n+      neighbor 1.1.1.2 maximum-routes 12000 \n    !\n    vrf test2\n-      neighbor 2.2.2.2 remote-as 2\n-      neighbor 2.2.2.2 maximum-routes 12000 \n+      neighbor 2.2.2.3 remote-as 2\n+      neighbor 2.2.2.3 maximum-routes 12000 \n !\n management api http-commands\n    no shutdown\n'
        self.device.load_candidate_config(filename='configs/new_good.conf')
        diff = self.device.compare_config()
        self.assertEqual(unicode(diff), unicode(intended_diff))

    def test_loading_modified_config_replace_config_and_rollback(self):
        self.device.load_candidate_config(filename='configs/new_good.conf')
        orig_diff = self.device.compare_config()
        self.device.replace_config()
        replace_config_diff = self.device.compare_config()
        self.device.rollback()
        last_diff = self.device.compare_config()

        result = (orig_diff == last_diff) and ( len(replace_config_diff) == 0 )

        self.assertTrue(result)

    def test_get_interface_config(self):
        config = self.device.get_config()
        interface = config['interface Ethernet2']
        self.assertGreater(len(interface), 0)