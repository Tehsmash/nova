# Copyright 2015 Cisco Systems
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
A driver wrapping the Ironic API, such that Nova may provision
bare metal resources.
"""
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
import six

from nova.compute import task_states
from nova.compute import vm_states
from nova import exception
from nova.i18n import _
from nova.i18n import _LE
from nova.i18n import _LI
from nova.openstack.common import loopingcall
from nova.virt import configdrive
from nova.virt.ironic import ironic_driver
from nova.virt.ironic import ironic_states

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


class CiscoIronicDriver(ironic_driver.IronicDriver):
    """Hypervisor driver for Ironic - bare metal provisioning."""

    def macs_for_instance(self, instance):
        return None

    def _plug_vifs(self, node, instance, network_info):
        node_uuid = instance.get('node')
        for vif in network_info:
            net_info = {
                'vlan': vif.segmentation_id,
                'mac-address': vif.mac,
                'uuid': vif['id']
            }
            self.ironicclient.call("node.vendor_passthru", node_id=node_uuid,
                                   method="add_vnic",
                                   args=net_info)

    def _unplug_vifs(self, node, instance, network_info):
        node_uuid = instance.get('node')
        # Delete vnics from UCS for this node via vendor passthru
        for vif in network_info:
            net_info = {
                'uuid': vif['id']
            }
            self.ironicclient.call("node.vendor_passthru", node_id=node_uuid,
                                   method="delete_vnic",
                                   args=net_info)
